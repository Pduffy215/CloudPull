from BuildPanelBin import build_panelinfo_bin
from datetime import datetime


def get_bin_info(json_body):

    scales = json_body["panelInfo"]["full_scale_voltages"]

    icp = [v == "True" for v in json_body["panelInfo"]["icp_on_status"]]

    pi = json_body["panelInfo"]

    panel_bin = {
        "fmax_calc_1_g": pi["Fmax1"],
        "fmax_calc_2_g": pi["Fmax2"],
        "fmax_calc_3_g": pi["Fmax3"],
        "res_l_1_g": pi["lines_res1"],
        "res_l_2_g": pi["lines_res2"],
        "res_l_3_g": pi["lines_res3"],
        "time_stream_start": datetime.strptime(
            pi["time_stream_start"], "%Y-%m-%d %H:%M:%S"
        ),
        "time_stream_stop": datetime.strptime(
            pi["time_stream_stop"], "%Y-%m-%d %H:%M:%S"
        ),
        "rpm_g": pi["one_x_rpm"],
        "database_link_2": pi["database_link2"],
        "database_link_3": pi["database_link3"],
        "session_path": pi["session_path"],
        "session_name": pi["session_name"],
        "stream_gaps": pi["num_stream_gaps"],
        "site_name_g": json_body["site_name"],
        "mach_name_g": json_body["machine_name"],
        "equip_name_g": json_body["equipment_name"],
        "shaft_name_g": json_body["shaft_name"],
        "bearing_name_g": json_body["bearing_name"],
        "trans_name_g":  json_body["transducer_name"],
        "transd_type_g": pi["transducerType"],
        "transd_type": pi["transducerType"],
        "probe_dir": pi["probe_dir"],
        "universal_company": json_body["company_name"],
        "universal_site": json_body["site_name"],

        # route / panel ID cluster 
        "route_count":        pi.get("route_count", 0),
        "panel_id_1f_g":      pi.get("panel_id_1f", 0),
        "panel_id_2f_g":      pi.get("panel_id_2f", 0),
        "panel_id_3f_g":      pi.get("panel_id_3f", 0),
        "panel_id_1w_g":      pi.get("panel_id_1w", 0),
        "panel_id_2w_g":      pi.get("panel_id_2w", 0),
        "panel_id_3w_g":      pi.get("panel_id_3w", 0),
        "panel_id_1_env_g":   pi.get("panel_id_1_env", 0),
        "panel_id_2_env_g":   pi.get("panel_id_2_env", 0),
        "panel_id_3_env_g":   pi.get("panel_id_3_env", 0),
        "panel_cnt":          pi.get("panel_cnt", 0),

        #  envelope flags  
        "envelope_r1_g": pi.get("envelope_r1", False),
        "envelope_r2_g": pi.get("envelope_r2", False),
        "envelope_r3_g": pi.get("envelope_r3", False),

        #  orientation 
        "mach_dir": pi.get("mach_dir", ""),

        #  timing / gap analysis 
        "updatedRefTime":         pi.get("updatedRefTime", 0.0),
        "timeToFillBuffer":       pi.get("timeToFillBuffer", 0.0),
        "deltaTimeSD":            pi.get("deltaTimeSD", 0.0),
        "numGapsOut":             pi.get("numGapsOut", 0),
        "deltaTimeForLastGap":    pi.get("deltaTimeForLastGap", 0.0),
        "biggestDeltaTime_NoGap": pi.get("biggestDeltaTime_NoGap", 0.0),
        "gapRefTimes":            pi.get("gapRefTimes", []),
        "startTime":              pi.get("startTime", 0.0),

        # measurement location / route 
        "stream_time_g":     pi.get("stream_time_g", 0.0),
        "route_name_picked": pi.get("route_name_picked", ""),
        "meas_loc_id_in_g":  pi.get("meas_loc_id_in_g", 0),
        "segment_id_in_g":   pi.get("segment_id_in_g", 0),
        "mloc_array_g":      pi.get("mloc_array_g", []),

        # trailing fields 
        "trailing_fmax_g":    pi.get("trailing_fmax_g", 0.0),
        "trailing_unknown_g": pi.get("trailing_unknown_g", 0.0),

        "dataQuality": [
            {
                "badData": pi["data_quality_bad?"][i] == "True",
                "skiSlope": pi["data_quality_ski_slope?"][i] == "True",
                "1xNotPresent": pi["data_quality_1x_present?"][i] == "True",
                "levelsTooLow": pi["data_quality_bad_levels_too_low?"][i] == "True",
                "dataQualityIndex": pi["data_quality_index(0-10)"][i],
            }
            for i in range(len(pi["data_quality_index(0-10)"]))
        ],
    }
    return scales, icp, panel_bin


def test_get_bin_info():


    json_body = {
    "bearing_name": "BOTTOM BRG",
    "brg_type": "",
    "brg_vsc_id": "19",
    "company_api_key": "f044dcf1-1b55-4411-80a4-9530bcfe1046",
    "company_name": "WALMART DC 6858",
    "component_api_key": "",
    "customer_api_key": "9215cf4e-b72f-4aa0-90a2-69ee9dc00618",
    "equip_type": "",
    "equipment_name": "COMPRESSOR",
    "equipment_vsc_id": "9",
    "field": "testing",
    "fileProperties": {
        "Fmax": 40000.0,
        "Sampling_rate": 102400,
        "comments": "",
        "data_len_per_ch": 3688800,
        "delta_T": 9.765625e-06,
        "file_date_time": "2025-11-24 07:53:49",
        "file_size": 59020836,
        "first_byte_code": 1,
        "len_min": 0.6666666666666666,
        "len_sec": 40.230318,
        "num_active_chs": 4,
        "total_array_size": 14755200
    },
    "machine_api_key": "",
    "machine_name": "C-1",
    "machine_vsc_id": "2",
    "meas_loc_trans_vsc_id": "19",
    "measurement_start_time": "2025-11-24 07:53:49",
    "panelInfo": {
        "Fmax1": 500,
        "Fmax2": 10000,
        "Fmax3": 10000,
        "data_quality_1x_present?": [
        "False",
        "False",
        "False",
        "False"
        ],
        "data_quality_bad?": [
        "False",
        "False",
        "False",
        "False"
        ],
        "data_quality_bad_levels_too_low?": [
        "False",
        "False",
        "False",
        "False"
        ],
        "data_quality_index(0-10)": [
        0,
        0,
        0,
        0
        ],
        "data_quality_ski_slope?": [
        "False",
        "False",
        "False",
        "False"
        ],
        "database_link2": "C:\\VSC\\WinProtect\\COMPANY000005\\SITE000000.sit",
        "database_link3": "C:\\VSC\\WinProtect\\COMPANY000005\\SITE000001.sit",
        "full_scale_voltages": [
        0.1,
        0.2,
        0.5,
        0.1,
        10.0,
        10.0,
        10.0,
        10.0
        ],
        "icp_on_status": [
        "True",
        "True",
        "True",
        "True",
        "False",
        "False",
        "False",
        "False"
        ],
        "lines_res1": "800",
        "lines_res2": "6400",
        "lines_res3": "25600",
        "num_stream_gaps": 0,
        "one_x_rpm": 1950,
        "probe_dir": "Top",
        "session_name": "C_1_BOTTOM_BRG_Triax_251124_045346",
        "session_path": "C:\\WALMART DC 6858\\C_1_BOTTOM_BRG_Triax_251124_045346",
        "time_stream_start": "2025-11-24 07:53:49",
        "time_stream_stop": "2025-11-24 07:54:29",
        "transducerType": 666
    },
    "provider_api_key": "1f3992f3-79fd-4210-95f5-6bf3412ae2e6",
    "provider_name": "VSC_DEV4",
    "server_url": "http://vscprotect.twintechlabs.io",
    "shaft_name": "RIGHT GATE ROTOR",
    "shaft_type": "",
    "shaft_vsc_id": "15",
    "signal_api_key": "",
    "site_name": "MEBANE NC",
    "survey_api_key": "5af04179-282c-4f72-a40a-bb79184a5b4d",
    "survey_number": "1",
    "transducer_name": "Triax",
    "vsc_site_key": "9215cf4e-b72f-4aa0-90a2-69ee9dc00618"
    }

    scales, icp, panel_bin = get_bin_info(json_body)
    print(f"\nScales: {scales}\n")
    print(f"ICP: {icp}\n")
    print(f"Panel_BIN: {panel_bin}\n")
    
    # build_panelinfo_bin(panel_bin, scales, icp)


if __name__ == "__main__":
    test_get_bin_info()