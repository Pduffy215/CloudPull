from Config import ARCA_API_KEY, ARCA_URL
from GetArcaKeys import get_arca_keys
from Post_it import post_it
import getpass


def post_streams_log(no_machines, no_bearings, full_json, measurement_start_time, posted_pulled, log_gmt, min_mbps, max_mbps, avg_mbps, pushed_log):
    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_LOG", "Streams_Log")   # Arca Log index key

    json_data = {"provider_name":          full_json["provider_name"],
                 "company_name":           full_json["company_name"],
                 "site_name":              full_json["site_name"],
                 "survey_no":              full_json["survey_number"],      # Log Post format
                 "no_machines":            no_machines,
                 "no_bearings":            no_bearings,
                 "measurement_start_time": measurement_start_time,
                 "posted_or_pulled?":      posted_pulled,
                 "log_gmt":                log_gmt,
                 "username":               getpass.getuser(),
                 "pull_stats":             {"min_mbps":               min_mbps,
                                            "max_mbps":               max_mbps,
                                            "avg_mbps":               avg_mbps,
                                            "pulled_by":              getpass.getuser()},
                 "push_stats":             {"min_mbps":               pushed_log['push_stats']['min_mbps'],
                                            "max_mbps":               pushed_log['push_stats']['max_mbps'],
                                            "avg_mbps":               pushed_log['push_stats']['avg_mbps'],
                                            "posted_by":              pushed_log['push_stats']['posted_by']}
                 }


    success, response = post_it(
        enable_server=True,
        milliseconds_wait=500,
        server_address=f"{ARCA_URL}/indices/documents/write?api_key={ARCA_API_KEY}&idx_key={idx_key}", 
        max_short_iterations=1,
        max_long_iterations=0,
        json_data=json_data
    )




def test_post_streams_log():
    
    json_data = {
     "company_api_key": "af98f58f-c615-4632-bb62-f7e80db5376c",
     "vsc_site_key": "df6af317-c563-421c-a25c-855adf007550",
     "survey_number": "1",
     "machine_vsc_id": "2",
     "equipment_vsc_id": "9",
     "server_url": "http://vscprotect.twintechlabs.io",
     "provider_name": "IR PROS",
     "company_name": "PRODUCERS DAIRY",
     "site_name": "FAIRFIELD CA",                     # This Posts a Test Stream Log
     "machine_name": "C-1",
     "equipment_name": "COMPRESSOR",
     "shaft_name": "RIGHT GATE ROTOR",
     "bearing_name": "BOTTOM BRG",
     "transducer_name": "Triax",
     "measurement_start_time": "2025-11-24 07:53:49"
    }
    
    measurement_start_time = "2025-11-24 07:53:49"
    log_gmt = 3
    min_mbps = 2
    max_mbps = 2
    avg_mbps = 2

    post_streams_log(6, 39, json_data, measurement_start_time, "Posted", log_gmt, min_mbps, max_mbps, avg_mbps)

if __name__ == "__main__":
    test_post_streams_log()