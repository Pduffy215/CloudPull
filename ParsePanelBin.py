import struct
from datetime import datetime, timezone


class Cursor:

    def __init__(self, data):
        self.data = data  # raw bytes of the file
        self.pos = 0  # current read offset

    def read_u32(self):
        val = struct.unpack(">I", self.data[self.pos:self.pos + 4])[0]  # big-endian unsigned 32-bit
        self.pos += 4
        return val

    def read_i32(self):
        val = struct.unpack(">i", self.data[self.pos:self.pos + 4])[0]  # big-endian signed 32-bit
        self.pos += 4
        return val

    def read_i16(self):
        val = struct.unpack(">h", self.data[self.pos:self.pos + 2])[0]  # big-endian signed 16-bit
        self.pos += 2
        return val

    def read_u16(self):
        val = struct.unpack(">H", self.data[self.pos:self.pos + 2])[0]  # big-endian unsigned 16-bit
        self.pos += 2
        return val

    def read_sgl(self):

        val = struct.unpack(">f", self.data[self.pos:self.pos + 4])[0] # LabVIEW 'single' = 32-bit float.
        self.pos += 4
        return val

    def read_dbl(self):

        val = struct.unpack(">d", self.data[self.pos:self.pos + 8])[0] # LabVIEW 'double' = 64-bit float.
        self.pos += 8
        return val

    def read_bool(self):
        val = bool(self.data[self.pos])  # single byte, nonzero = true
        self.pos += 1
        return val

    def read_pascal_string(self):
        length = struct.unpack(">I", self.data[self.pos:self.pos + 4])[0]  # 4-byte length prefix
        self.pos += 4
        val = self.data[self.pos:self.pos + length].decode("ascii")  # then raw ascii bytes
        self.pos += length
        return val

    def read_labview_timestamp(self):

        seconds = struct.unpack(">q", self.data[self.pos:self.pos + 8])[0]  # signed 64-bit seconds since 1904
        self.pos += 16  # 8 bytes seconds + 8 bytes fraction (fraction discarded)
        labview_epoch_offset = 2082844800  # seconds between 1904-01-01 and 1970-01-01
        utc_dt = datetime.fromtimestamp(seconds - labview_epoch_offset, tz=timezone.utc)  # convert to Unix epoch UTC
        return utc_dt.replace(tzinfo=None)  # strip tzinfo, return naive datetime in GMT/UTC

    def read_labview_path(self):

        magic = self.data[self.pos:self.pos + 4]      
        assert magic == b"PTH0", f"expected PTH0 magic at 0x{self.pos:04x}, got {magic}"  # verify path type tag
        self.pos += 4  # advance past magic
        self.pos += 4  # total_len, redundant with segment-by-segment read
        segment_count = struct.unpack(">I", self.data[self.pos:self.pos + 4])[0]
        self.pos += 4  # advance past segment_count
        segments = []
        for _ in range(segment_count):
            seg_len = self.data[self.pos]  # 1-byte length per segment
            self.pos += 1
            segments.append(self.data[self.pos:self.pos + seg_len].decode("ascii"))
            self.pos += seg_len
        if segments:
            return segments[0] + ":\\" + "\\".join(segments[1:])  # rebuild "C:\VSC\..." form
        return ""

    def read_data_quality_array(self):

        count = self.read_i32()  # element count prefix
        entries = []
        for _ in range(count):  # one entry per data quality record
            entries.append({
                "badData": self.read_bool(),  # bad data flag
                "skiSlope": self.read_bool(),  # ski slope flag
                "1xNotPresent": self.read_bool(),  # 1x not present flag
                "levelsTooLow": self.read_bool(),  # levels too low flag
                "dataQualityIndex": self.read_i16(),  # quality index score
            })
        return entries

    def read_dbl_array(self):
        count = self.read_i32()  # element count prefix
        return [self.read_dbl() for _ in range(count)]  # read count doubles in sequence

    def read_u16_array(self):
        count = self.read_i32()  # element count prefix
        return [self.read_u16() for _ in range(count)]  # read count u16s in sequence

def parse_panelinfo_bin(path):

    with open(path, "rb") as f:
        data = f.read()  # load entire binary file into memory

    c = Cursor(data)
    panel_bin = {}

    panel_bin["route_count"] = c.read_u32()
    for name in ["panel_id_1f_g", "panel_id_2f_g", "panel_id_3f_g",
                 "panel_id_1w_g", "panel_id_2w_g", "panel_id_3w_g",
                 "panel_id_1_env_g", "panel_id_2_env_g", "panel_id_3_env_g"]:
        panel_bin[name] = c.read_u32()  # 9 panel ID fields (freq/waveform/envelope x3)

    panel_bin["fmax_calc_1_g"] = c.read_sgl()
    panel_bin["fmax_calc_2_g"] = c.read_sgl()
    panel_bin["fmax_calc_3_g"] = c.read_sgl()  # calculated Fmax per channel

    panel_bin["res_l_1_g"] = c.read_pascal_string()
    panel_bin["res_l_2_g"] = c.read_pascal_string()
    panel_bin["res_l_3_g"] = c.read_pascal_string()  # resolution labels per channel

    panel_bin["time_stream_stop"] = c.read_labview_timestamp()
    panel_bin["time_stream_start"] = c.read_labview_timestamp()  # note: stop read before start

    panel_bin["rpm_g"] = c.read_sgl()  # machine RPM at time of stream

    scales_raw = [c.read_pascal_string() for _ in range(8)]  # 8 scale strings, e.g. "0.20" or "10V"
    scales = [float(s.rstrip("Vv")) for s in scales_raw]  # strip trailing V/v to get numeric value

    panel_bin["database_link_2"] = c.read_labview_path()
    panel_bin["database_link_3"] = c.read_labview_path()
    panel_bin["session_path"] = c.read_labview_path()  # 3 LabVIEW-format paths

    panel_bin["session_name"] = c.read_pascal_string()
    panel_bin["stream_gaps"] = c.read_u32()  # count of gaps detected in stream

    panel_bin["site_name_g"] = c.read_pascal_string()
    panel_bin["mach_name_g"] = c.read_pascal_string()
    panel_bin["equip_name_g"] = c.read_pascal_string()
    panel_bin["shaft_name_g"] = c.read_pascal_string()
    panel_bin["bearing_name_g"] = c.read_pascal_string()
    panel_bin["trans_name_g"] = c.read_pascal_string()  # site/machine/equip/shaft/bearing/transducer names

    panel_bin["panel_cnt"] = c.read_u32()
    panel_bin["transd_type_g"] = c.read_i32()  # global transducer type code

    panel_bin["envelope_r1_g"] = c.read_bool()
    panel_bin["envelope_r2_g"] = c.read_bool()
    panel_bin["envelope_r3_g"] = c.read_bool()  # envelope-enabled flags per channel

    panel_bin["mach_dir"] = c.read_pascal_string()
    panel_bin["probe_dir"] = c.read_pascal_string()
    panel_bin["universal_company"] = c.read_pascal_string()
    panel_bin["universal_site"] = c.read_pascal_string()

    # Value cluster (8 elements) 
    panel_bin["updatedRefTime"] = c.read_dbl()
    panel_bin["timeToFillBuffer"] = c.read_dbl()
    panel_bin["deltaTimeSD"] = c.read_dbl()
    panel_bin["numGapsOut"] = c.read_i32()   # LONG, not DBL 
    panel_bin["deltaTimeForLastGap"] = c.read_dbl()
    panel_bin["biggestDeltaTime_NoGap"] = c.read_dbl()
    panel_bin["gapRefTimes"] = c.read_dbl_array()   # real array
    panel_bin["startTime"] = c.read_dbl()
    # end Value cluster

    panel_bin["dataQuality"] = c.read_data_quality_array()  

    icp = [c.read_bool() for _ in range(8)]  # ICP power-enabled flags, one per channel

    panel_bin["stream_time_g"] = c.read_dbl()
    panel_bin["route_name_picked"] = c.read_pascal_string()
    panel_bin["meas_loc_id_in_g"] = c.read_i32()
    panel_bin["segment_id_in_g"] = c.read_i32()
    panel_bin["transd_type"] = c.read_i32()  # 2nd TRANSD_TYPE g occurrence

    panel_bin["mloc_array_g"] = c.read_u16_array()  # measurement location ID array

    
    panel_bin["trailing_fmax_g"] = c.read_dbl()   # = 40000.0 in both files
    panel_bin["trailing_unknown_g"] = c.read_dbl()  # varies per file

    # The file should be fully consumed now.
    remaining = len(data) - c.pos
    if remaining != 0:
        raise ValueError(
            f"Parser finished with {remaining} bytes unaccounted for "
            f"(expected exactly 0)."
        )

    # TRANSD_TYPE appears twice and must always agree.
    if panel_bin["transd_type"] != panel_bin["transd_type_g"]:
        raise ValueError(
            f"TRANSD_TYPE mismatch: {panel_bin['transd_type_g']} vs "
            f"{panel_bin['transd_type']} -- parsing drifted somewhere "
            f"upstream."
        )

    return panel_bin, scales, icp


def build_data_quality_fields(data_quality):
    def as_str_bool(b):
        return "true" if b else "false"  # convert Python bool to lowercase string for JSON payload

    return {
        "data_quality_bad?": [as_str_bool(d["badData"]) for d in data_quality],
        "data_quality_ski_slope?": [as_str_bool(d["skiSlope"]) for d in data_quality],
        "data_quality_1x_present?": [as_str_bool(d["1xNotPresent"]) for d in data_quality],
        "data_quality_bad_levels_too_low?": [as_str_bool(d["levelsTooLow"]) for d in data_quality],
        "data_quality_index(0-10)": [d["dataQualityIndex"] for d in data_quality],
    }


if __name__ == "__main__":
    path = r"C:\Users\PCduffy\Projects\CloudUpload\Streams\WALMART DC 6858\C_1_BOTTOM_BRG_Triax_251124_045346\PANELINFO.BIN"
    
    panel_bin, scales, icp = parse_panelinfo_bin(path)

    print(f"\nScales: {scales}\n")
    print(f"ICP: {icp}\n")
    print(f"Panel_BIN: {panel_bin}\n")