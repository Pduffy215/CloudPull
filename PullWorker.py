from PyQt5.QtCore import QThread, pyqtSignal
from Config import ARCA_API_KEY, ARCA_URL, CONFIG_DIR, LOG_FILE, PULLED_STREAMS_DIR
from GetArcaKeys import get_arca_keys
from SearchArcaMatch import search_arca_match
from Base64ToVolts import base64_to_int32_array, int32_to_volts
from BuildPanelBin import build_panelinfo_bin
from monitorLogWrapper import monitorLogWrapper
from BuildWaveformBin import build_waveform_bin
from GetBinInfo import get_bin_info
from JSONSoundToWave import json_sound_to_wav
from PostStreamsLog import post_streams_log
from PullText import write_misc_files
from datetime import datetime, timezone
import getpass
import requests
import time
import sys
import os
import re

sys.stdout = open(os.path.join(CONFIG_DIR, "debug_output.txt"), "w", buffering=1)
sys.stderr = sys.stdout

def safe_name(s: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '-', str(s)).strip().rstrip('.')

class PullWorker(QThread):
    # runs the network/file work off the GUI thread so the window never freezes
    progress = pyqtSignal(int, int, str)          # count, total, prefix
    finished_ok = pyqtSignal()                     # emitted when the whole pull completes cleanly
    failed = pyqtSignal(str)                        # emitted with an error message on failure
    error_occurred = pyqtSignal(str, str)            # (title, message) for per-item errors surfaced to the GUI
    update_speed = pyqtSignal(int, int, int)         # current, min, max Mbps for the speed readout

    def __init__(self, measurement_start_time, data):
        super().__init__()
        self.measurement_start_time = measurement_start_time  # survey start time, used for the streams log entry
        self.data = data                                       # the survey/query payload passed in from the GUI

    def run(self):

        data = self.data
        print(f"Pulling {data['partitions']['company_name']} Survey #{data['indices']['survey_number']}\n")
        monitorLogWrapper(True, 0, "\n\n" + "STREAM PULLER", "Starting Stream Puller", LOG_FILE)

        # resolve output folder + figure out what's already been pulled
        dt = datetime.strptime(self.measurement_start_time, "%Y-%m-%d %H:%M:%S")
        result = dt.strftime("%m_%d_%y")
        output_folder = os.path.join(PULLED_STREAMS_DIR, safe_name(f"{data['partitions']['company_name']}_{result} Pulled"))
        local_log_output_path = os.path.join(CONFIG_DIR, "Local_Log.txt")

        try:
            already_pulled = set(os.listdir(output_folder))  # existing folder names, used to skip re-downloads
        except FileNotFoundError:
            already_pulled = set()  # first run, nothing pulled yet

        # fetch the list of documents to pull for this survey
        try:
            idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VIBRATION SPECIALTY CORP", "VSC Default")
            documents = search_arca_match(idx_key, data)
        except Exception as e:
            monitorLogWrapper(True, 1, "ARCA", "Couldn't Get Arca Documents", LOG_FILE)
            self.failed.emit(str(e))  # can't get the doc list
            return

        if not documents:
            monitorLogWrapper(True, 1, "ARCA", "Couldn't Get Arca Documents", LOG_FILE)
            self.failed.emit("No Documents for current Survey")
            return

        count = 1
        machine_count = 0
        seen_machine = set()   # tracks distinct machine names seen, for the log summary
        min_mbps = None
        max_mbps = None
        mbps_list = []
        monitorLogWrapper(True, 1, f"\n     STREAM PULLER", f"Pulling {data['partitions']['company_name']} Survey #{data['indices']['survey_number']}", LOG_FILE)

        for doc in documents:
            if self.isInterruptionRequested():   # user hit cancel
                monitorLogWrapper(True, 0, "STREAM PULLER", "Cancelled by User", LOG_FILE)
                self.failed.emit("Cancelled by user")
                return

            monitorLogWrapper(True, 2, f"\n          STREAM PULLER", f"Pulling {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}", LOG_FILE)
            bearing_id = doc.get('partitions', {}).get('bearing_name', doc.get('api_key', 'unknown'))  # used by all except below

            # build this stream's output path, skip if already pulled
            try:
                doc_start = time.monotonic()  # timer for this doc's download speed
                ts = datetime.fromisoformat(doc["indices"]["measurement_start_time"])
                folder_name = safe_name(f"{doc['partitions']['machine_name']}_{doc['indices']['bearing_name'].replace(' ', '_')}_Triax_{ts:%y%m%d_%H%M%S}")
                output_path = os.path.join(output_folder, folder_name)
            except Exception as e:
                self.error_occurred.emit("Bearing Failed", f"{bearing_id}\n\n{e}")
                self.failed.emit(str(e))
                return

            if folder_name in already_pulled:
                self.progress.emit(count, len(documents), f"{doc['partitions']['machine_name']} {doc['indices']['bearing_name']} (already pulled, skipping)")
                monitorLogWrapper(True, 2, "STREAM PULLER", f"Skipping {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}", LOG_FILE)
                print(f"Skipping {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}")
                count += 1
                continue  # skip download, already have this one

            # download the document + track transfer speed 
            try:
                response = requests.get(f"{ARCA_URL}/indices/document", params={"api_key": ARCA_API_KEY, "doc_key": doc["api_key"]}, timeout=30)
                response.raise_for_status()

                doc_bytes = len(response.content)
                elapsed = time.monotonic() - doc_start
                mbps = (doc_bytes * 8 / 1_000_000) / elapsed if elapsed > 0 else 0
                min_mbps = round(mbps) if (min_mbps is None or mbps < min_mbps) else min_mbps
                max_mbps = round(mbps) if (max_mbps is None or mbps > max_mbps) else max_mbps
                mbps_list.append(mbps)
                self.update_speed.emit(int(mbps), int(min_mbps), int(max_mbps))

                json_body = response.json()
            except Exception as e:
                monitorLogWrapper(True, 2, "STREAM PULLER", f"Couldn't load Bearing: {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}", LOG_FILE)
                self.error_occurred.emit("Bearing Failed", f"{bearing_id}\n\n{e}")
                self.failed.emit(str(e))
                return

            monitorLogWrapper(True, 3, "STREAM PULLER", f"Bearing Successfully Loaded: {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}", LOG_FILE)

            # decode raw channel data from base64 into real volts
            try:
                raw_data = []
                full_scale_voltages = json_body["panelInfo"]["full_scale_voltages"]
                for i in range(4):  # 4 channels: 3 axes + reference/env
                    channel_volts = json_body["rawData"][i]
                    raw_int16 = base64_to_int32_array(channel_volts)
                    raw_data.append(int32_to_volts(raw_int16, full_scale=full_scale_voltages[i]))
                json_body["rawData"] = raw_data
            except Exception as e:
                self.error_occurred.emit("Bearing Failed", f"{bearing_id}\n\n{e}")
                self.failed.emit(str(e))
                return

            if json_body["machine_name"] not in seen_machine:
                machine_count += 1                         # count distinct machines for the log summary
                seen_machine.add(json_body["machine_name"])

            # build and write the .bin/.wav output files
            try:
                machine_name = doc.get("partitions", {}).get("machine_name") or "?"
                bearing_name = doc.get("indices", {}).get("bearing_name") or "?"
                label = f"{machine_name} {bearing_name}"

                panel_info = json_body.get("panelInfo") if json_body else None
                file_props = json_body.get("fileProperties") if json_body else None
                raw_data = json_body.get("rawData") if json_body else None
                sound_data = json_body.get("sound_data") if json_body else None
                misc_info = json_body.get("misc_info") if json_body else None

                os.makedirs(output_path, exist_ok=True)  # create the per-stream output folder either way

                # raw waveform bin — needs both fileProperties.Fmax and rawData
                if file_props and file_props.get("Fmax") is not None and raw_data is not None and panel_info:
                    ts = datetime.strptime(panel_info["time_stream_stop"], "%Y-%m-%d %H:%M:%S")
                    raw = build_waveform_bin(file_props["Fmax"], ts, raw_data)
                    raw_filepath = os.path.join(output_path, f"{folder_name}.bin")
                    with open(raw_filepath, "wb") as f:
                        f.write(raw)
                    monitorLogWrapper(True, 3, "STREAM PULLER", f"Raw Waveform Binary Successful: {label}", LOG_FILE)
                else:
                    monitorLogWrapper(True, 2, "STREAM PULLER", f"Raw Waveform Binary SKIPPED (missing data): {label}", LOG_FILE)

                # panel info bin — needs panelInfo
                if panel_info:
                    scales, icp, panel_bin = get_bin_info(json_body)
                    raw_bytes = build_panelinfo_bin(panel_bin, scales, icp)
                    panel_filepath = os.path.join(output_path, "PanelInfo.bin")
                    with open(panel_filepath, "wb") as f:
                        f.write(raw_bytes)
                    monitorLogWrapper(True, 3, "STREAM PULLER", f"Panel Info Binary Successful: {label}", LOG_FILE)
                else:
                    monitorLogWrapper(True, 2, "STREAM PULLER", f"Panel Info Binary SKIPPED (missing panelInfo): {label}", LOG_FILE)

                # sound data — needs sound_data
                if sound_data:
                    sound_filepath = os.path.join(output_path, "SoundVib.wav")
                    json_sound_to_wav(sound_data, sound_filepath)
                    monitorLogWrapper(True, 3, "STREAM PULLER", f"Sound Data Successful: {label}", LOG_FILE)
                else:
                    monitorLogWrapper(True, 2, "STREAM PULLER", f"Sound Data SKIPPED (no sound_data): {label}", LOG_FILE)

                # misc files — needs misc_info
                if misc_info:
                    write_misc_files(output_path, misc_info)
                    monitorLogWrapper(True, 3, "STREAM PULLER", f"Text Files Successful: {label}", LOG_FILE)
                else:
                    monitorLogWrapper(True, 2, "STREAM PULLER", f"Text Files SKIPPED (no misc_info): {label}", LOG_FILE)

                self.progress.emit(count, len(documents), label)


            except Exception as e:
                monitorLogWrapper(True, 2, "STREAM PULLER", f"Failed to Load Output Files: {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}", LOG_FILE)
                self.error_occurred.emit("Bearing Failed", f"{bearing_id}\n\n{e}")
                self.failed.emit(str(e))
                return

            monitorLogWrapper(True, 2, "STREAM PULLER", f"Stream Pulled Successfully: {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}", LOG_FILE)
            print(f"Pulled {doc['partitions']['machine_name']} {doc['indices']['bearing_name']}")
            count += 1

        # update the streams log once all documents are pulled
        try:
            monitorLogWrapper(True, 1, f"\n     STREAM PULLER", f"Successfully Pulled: {data['partitions']['company_name']} Survey #{data['indices']['survey_number']}", LOG_FILE)

            idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_LOG", "Streams_Log")
            json_query = {
                "partitions": {"provider_name": data["partitions"]["provider_name"],
                            "company_name": data["partitions"]["company_name"],
                            "site_name": data["partitions"]["site_name"]},
                "indices": {"survey_no": data["indices"]["survey_number"]},
            }
            log_response = search_arca_match(idx_key, json_query)

            json_query["indices"]["posted_or_pulled?"] = "Posted"
            log_push_response = search_arca_match(idx_key, json_query)

            if not log_push_response:
                raise ValueError(f"No 'Posted' streams-log entry found for survey #{data['indices']['survey_number']}")

            response = requests.get(f"{ARCA_URL}/indices/document",
                                    params={"api_key": ARCA_API_KEY, "doc_key": log_push_response[0]["api_key"]},
                                    timeout=30)
            response.raise_for_status()
            pushed_log = response.json()

            log_gmt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            avg_mbps = round(sum(mbps_list) / len(mbps_list)) if mbps_list else 0

            if len(log_response) == 1:
                log_data = {"provider_name": data["partitions"]["provider_name"],
                            "company_name": data["partitions"]["company_name"],
                            "site_name": data["partitions"]["site_name"],
                            "survey_number": data["indices"]["survey_number"]}
                post_streams_log(machine_count, len(documents), log_data, self.measurement_start_time,
                                "Pulled", log_gmt, min_mbps, max_mbps, avg_mbps, pushed_log)

            with open(local_log_output_path, "a") as f:
                f.write(
                    f"\nPulled {data['partitions']['company_name']} Survey #{data['indices']['survey_number']}\n"
                    f"                        log_gmt: {log_gmt},\n"
                    f"                        measurement_start_time: {self.measurement_start_time},\n"
                    f"                        no_bearings: {len(documents)},\n"
                    f"                        no_machines: {machine_count},\n"
                    f"                        posted_or_pulled?: Pulled,\n"
                    f"                        survey_no: {data['indices']['survey_number']},\n"
                    f"                        username: {getpass.getuser()},\n"
                    f"                        pull_stats:\n"
                    f"                            min_Mbps: {min_mbps},\n"
                    f"                            max_Mbps: {max_mbps},\n"
                    f"                            avg_Mbps: {avg_mbps},\n"
                    f"                            pulled_by: {getpass.getuser()}\n"
                    f"                        push_stats:\n"
                    f"                            min_Mbps: {pushed_log['push_stats']['min_mbps']},\n"
                    f"                            max_Mbps: {pushed_log['push_stats']['max_mbps']},\n"
                    f"                            avg_Mbps: {pushed_log['push_stats']['avg_mbps']},\n"
                    f"                            posted_by: {pushed_log['push_stats']['posted_by']}\n"
                )

        except Exception as e:
            self.error_occurred.emit("Log Update Failed", f"Data was pulled successfully, but the streams log update failed:\n\n{e}")
            monitorLogWrapper(True, 0, f"   STREAM PULLER", "Arca Log Update Failed", LOG_FILE)
            monitorLogWrapper(True, 0, "\n\n" + "STREAM PULLER", "Finished Stream Puller", LOG_FILE)
            self.finished_ok.emit()   # data itself is fine — still tell the GUI the pull is done
            return
        
        monitorLogWrapper(True, 0, "\n" + "STREAM PULLER", "Finished Stream Puller", LOG_FILE)
        self.finished_ok.emit()  # signal the GUI that the pull completed