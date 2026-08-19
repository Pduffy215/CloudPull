import struct
from ParsePanelBin import parse_panelinfo_bin
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class Writer:
    def __init__(self):
        self.chunks = []  # accumulates byte chunks to join at the end

    def write_u32(self, val):
        self.chunks.append(struct.pack(">I", val))  # big-endian unsigned 32-bit

    def write_i32(self, val):
        self.chunks.append(struct.pack(">i", val))  # big-endian signed 32-bit

    def write_i16(self, val):
        self.chunks.append(struct.pack(">h", val))  # big-endian signed 16-bit

    def write_u16(self, val):
        self.chunks.append(struct.pack(">H", val))  # big-endian unsigned 16-bit

    def write_sgl(self, val):
        self.chunks.append(struct.pack(">f", val))  # LabVIEW single-precision float

    def write_dbl(self, val):
        self.chunks.append(struct.pack(">d", val))  # LabVIEW double-precision float

    def write_bool(self, val):
        self.chunks.append(bytes([1 if val else 0]))  # single byte, 1 or 0

    def write_pascal_string(self, val):
        encoded = val.encode("ascii")
        self.chunks.append(struct.pack(">I", len(encoded)))  # 4-byte length prefix
        self.chunks.append(encoded)  # then raw ascii bytes

    def write_labview_timestamp(self, dt):
        utc_dt = dt.replace(tzinfo=timezone.utc)  # tag naive dt as UTC/GMT directly
        labview_epoch_offset = (
            2082844800  # seconds between LabVIEW epoch (1904) and Unix epoch (1970)
        )
        unix_seconds = int(utc_dt.timestamp())
        labview_seconds = unix_seconds + labview_epoch_offset
        self.chunks.append(struct.pack(">q", labview_seconds))  # signed 64-bit seconds
        self.chunks.append(struct.pack(">Q", 0))  # fraction, not preserved

    def write_labview_path(self, path_str):
        if not path_str:
            self.chunks.append(b"PTH0")  # LabVIEW path type tag
            self.chunks.append(struct.pack(">I", 4))  # total_len: just the count field
            self.chunks.append(struct.pack(">I", 0))  # segment_count = 0
            return

        # "C:\VSC\WinProtect\..." -> ["C", "VSC", "WinProtect", ...]
        drive, _, rest = path_str.partition(":\\")
        segments = [drive] + rest.split("\\") if rest else [drive]

        segment_bytes = b""
        for seg in segments:
            seg_encoded = seg.encode("ascii")
            segment_bytes += (
                bytes([len(seg_encoded)]) + seg_encoded
            )  # 1-byte len + ascii per segment

        self.chunks.append(b"PTH0")
        self.chunks.append(struct.pack(">I", 4 + len(segment_bytes)))  # total_len
        self.chunks.append(struct.pack(">I", len(segments)))  # segment_count
        self.chunks.append(segment_bytes)

    def write_dbl_array(self, values):
        self.write_i32(len(values))  # element count prefix
        for v in values:
            self.write_dbl(v)

    def write_u16_array(self, values):
        self.write_i32(len(values))  # element count prefix
        for v in values:
            self.write_u16(v)

    def write_data_quality_array(self, entries):
        self.write_i32(len(entries))  # element count prefix
        for e in entries:
            self.write_bool(e.get("badData", False))
            self.write_bool(e.get("skiSlope", False))
            self.write_bool(e.get("1xNotPresent", False))
            self.write_bool(e.get("levelsTooLow", False))
            self.write_i16(e.get("dataQualityIndex", 0))

    def get_bytes(self):
        return b"".join(self.chunks)  # flatten all chunks into final byte string


# Fallback for each field so it wouldnt break whole file if not there.
_FIELD_DEFAULTS = {
    "route_count": 0,
    "panel_id_1f_g": 0,
    "panel_id_2f_g": 0,
    "panel_id_3f_g": 0,
    "panel_id_1w_g": 0,
    "panel_id_2w_g": 0,
    "panel_id_3w_g": 0,
    "panel_id_1_env_g": 0,
    "panel_id_2_env_g": 0,
    "panel_id_3_env_g": 0,
    "fmax_calc_1_g": 0.0,
    "fmax_calc_2_g": 0.0,
    "fmax_calc_3_g": 0.0,
    "res_l_1_g": "",
    "res_l_2_g": "",
    "res_l_3_g": "",
    "time_stream_stop": datetime(1904, 1, 1),
    "time_stream_start": datetime(1904, 1, 1),
    "rpm_g": 0.0,
    "database_link_2": "",
    "database_link_3": "",
    "session_path": "",
    "session_name": "",
    "stream_gaps": 0,
    "site_name_g": "",
    "mach_name_g": "",
    "equip_name_g": "",
    "shaft_name_g": "",
    "bearing_name_g": "",
    "trans_name_g": "",
    "panel_cnt": 0,
    "transd_type_g": 0,
    "envelope_r1_g": False,
    "envelope_r2_g": False,
    "envelope_r3_g": False,
    "mach_dir": "",
    "probe_dir": "",
    "universal_company": "",
    "universal_site": "",
    "updatedRefTime": 0.0,
    "timeToFillBuffer": 0.0,
    "deltaTimeSD": 0.0,
    "numGapsOut": 0,
    "deltaTimeForLastGap": 0.0,
    "biggestDeltaTime_NoGap": 0.0,
    "gapRefTimes": [],
    "startTime": 0.0,
    "dataQuality": [],
    "stream_time_g": 0.0,
    "route_name_picked": "",
    "meas_loc_id_in_g": 0,
    "segment_id_in_g": 0,
    "transd_type": 0,
    "mloc_array_g": [],
    "trailing_fmax_g": 0.0,
    "trailing_unknown_g": 0.0,
}


def get_field(panel_bin, key):
    
    if key in panel_bin:
        return panel_bin[key]
    print(f"[build_panelinfo_bin] WARNING: '{key}' missing from panel_bin, using default {_FIELD_DEFAULTS[key]!r}")
    return _FIELD_DEFAULTS[key]


def build_panelinfo_bin(panel_bin, scales, icp):

    w = Writer()
    g = lambda key: get_field(panel_bin, key)

    w.write_u32(g("route_count"))  # number of routes in this panel
    for name in [
        "panel_id_1f_g",
        "panel_id_2f_g",
        "panel_id_3f_g",
        "panel_id_1w_g",
        "panel_id_2w_g",
        "panel_id_3w_g",
        "panel_id_1_env_g",
        "panel_id_2_env_g",
        "panel_id_3_env_g",
    ]:
        w.write_u32(g(name))  # 9 panel ID fields 

    w.write_sgl(g("fmax_calc_1_g"))
    w.write_sgl(g("fmax_calc_2_g"))
    w.write_sgl(g("fmax_calc_3_g"))  # calculated Fmax for each of 3 channels

    w.write_pascal_string(g("res_l_1_g"))
    w.write_pascal_string(g("res_l_2_g"))
    w.write_pascal_string(g("res_l_3_g"))  # resolution/lines labels per channel

    w.write_labview_timestamp(g("time_stream_stop"))
    w.write_labview_timestamp(g("time_stream_start"))  # stop written before start

    w.write_sgl(g("rpm_g"))  # machine RPM at time of stream

    for i, s in enumerate(scales):
        if i < 4:
            # Channels 1-4: plain decimal, no "V" suffix (e.g. "0.20")
            w.write_pascal_string(f"{s:.2f}")
        else:
            # Channels 5-8: whole-number voltage + "V" suffix (e.g. "10V")
            w.write_pascal_string(f"{s:g}V")

    w.write_labview_path(g("database_link_2"))
    w.write_labview_path(g("database_link_3"))
    w.write_labview_path(g("session_path"))  # 3 LabVIEW-format paths

    w.write_pascal_string(g("session_name"))
    w.write_u32(g("stream_gaps"))  # count of gaps detected in stream

    w.write_pascal_string(g("site_name_g"))
    w.write_pascal_string(g("mach_name_g"))
    w.write_pascal_string(g("equip_name_g"))
    w.write_pascal_string(g("shaft_name_g"))
    w.write_pascal_string(g("bearing_name_g"))
    w.write_pascal_string(g("trans_name_g"))  # site/machine/equip/shaft/bearing/transducer names

    w.write_u32(g("panel_cnt"))
    w.write_i32(g("transd_type_g"))  # global transducer type code

    w.write_bool(g("envelope_r1_g"))
    w.write_bool(g("envelope_r2_g"))
    w.write_bool(g("envelope_r3_g"))  # envelope-enabled flags per channel

    w.write_pascal_string(g("mach_dir"))
    w.write_pascal_string(g("probe_dir"))
    w.write_pascal_string(g("universal_company"))
    w.write_pascal_string(g("universal_site"))

    w.write_dbl(g("updatedRefTime"))
    w.write_dbl(g("timeToFillBuffer"))
    w.write_dbl(g("deltaTimeSD"))
    w.write_i32(g("numGapsOut"))
    w.write_dbl(g("deltaTimeForLastGap"))
    w.write_dbl(g("biggestDeltaTime_NoGap"))
    w.write_dbl_array(g("gapRefTimes"))  # variable-length array of gap timestamps
    w.write_dbl(g("startTime"))

    w.write_data_quality_array(g("dataQuality"))  # per-measurement quality flags array

    for b in icp:
        w.write_bool(b)  # ICP power-enabled flags, one bool per channel

    w.write_dbl(g("stream_time_g"))
    w.write_pascal_string(g("route_name_picked"))
    w.write_i32(g("meas_loc_id_in_g"))
    w.write_i32(g("segment_id_in_g"))
    w.write_i32(g("transd_type"))

    w.write_u16_array(g("mloc_array_g"))  # measurement location ID array

    w.write_dbl(g("trailing_fmax_g"))
    w.write_dbl(g("trailing_unknown_g"))  # trailing field, purpose still unconfirmed

    return w.get_bytes()


def test_build_panelinfo_bin():

    panelinfo_path = r"C:\Users\PCduffy\Projects\CloudUpload\Streams\WALMART DC 8852_06_19_26\C_1_OB_MTR_Triax_260619_080730\PANELINFO.BIN"
    panel_bin, scales, icp = parse_panelinfo_bin(
        panelinfo_path
    )  # round-trip: parse original file

    raw_bytes = build_panelinfo_bin(
        panel_bin, scales, icp
    )  # then rebuild it from parsed data

    output_path = r"C:\Users\PCduffy\Documents\PANELINFO_generated.bin"

    with open(output_path, "wb") as f:
        f.write(raw_bytes)

    print(f"Wrote {len(raw_bytes)} bytes to {output_path}")


if __name__ == "__main__":
    test_build_panelinfo_bin()