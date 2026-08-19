import json
from Config import LOG_FILE
from monitorLogWrapper import monitorLogWrapper
import requests
import time

# This function posts JSON data to a specified server with retry logic.
def post_it(enable_server, milliseconds_wait, server_address, max_short_iterations, max_long_iterations, json_data):
    # gate - if server is disabled (e.g. pause was pressed) skip posting
    if not enable_server:
        return False, ""

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    response = None
    data = json_data if isinstance(json_data, str) else json.dumps(json_data)

    # short retry loop - quick attempts with milliseconds_wait between each
    for attempt in range(max_short_iterations):
        try:
            response = requests.post(server_address, data=data, headers=headers, timeout=30)

            if response.status_code == 401:
                return False, "Unauthorized (401) - check API key and permissions"  # wrong API key - no point retrying
            
            elif response.ok:
                return True, response.text
            
        except Exception as e:
            monitorLogWrapper(True, 2, "PostIt", f"Attempt {attempt + 1} failed: {str(e)}", LOG_FILE)

        time.sleep(milliseconds_wait / 1000)  # convert ms to seconds

    # long retry loop - slower attempts with 30s delay between each
    # mirrors LabVIEW comment "long delay(s) of about 30s"
    for attempt in range(max_long_iterations):
        try:
            time.sleep(30)
            response = requests.post(server_address, data=data, headers=headers, timeout=30)
            if response.ok:

                return True, response.text
            
        except Exception as e:         # connection error - try again
            monitorLogWrapper(True, 2, "PostIt", f"Long attempt {attempt + 1} failed: {str(e)}", LOG_FILE)

    # all retries exhausted - mirrors LabVIEW label "Data posting failed after multiple attempts"
    if response is not None:
        print("Status code:", response.status_code)
        print("Response:", response.text)
        monitorLogWrapper(True, 2, "PostIt", f"Failed after multiple attempts - last status: {response.status_code}", LOG_FILE)
        return False, f"Failed after multiple attempts - last status: {response.status_code}"
    else:                                                # no response received at all
        monitorLogWrapper(True, 2, "PostIt", "Failed after multiple attempts - no response received", LOG_FILE)
        return False, "Failed after multiple attempts - no response received"
    

def test_post_it():
    ARCA_API_KEY = "7740a73c-f497-4d7f-8e68-200b071ff320"
    ARCA_URL = "http://vscarca.twintechlabs.io/"
    idx_key = "5e4afd7f-8529-45dd-a586-1b716161d18b"

    json_data = {
     "survey_number": "1",
     "provider_name": "Test",
     "company_name": "WALMART DC 6858",
     "site_name": "MEBANE NC",
     "machine_name": "C-1",
     "equipment_name": "COMPRESSOR",
     "shaft_name": "RIGHT GATE ROTOR",
     "bearing_name": "BOTTOM BRG",
     "transducer_name": "Triax",
     "measurement_start_time": "2025-11-24 07:53:49",
     
}


    success, response_text = post_it(
        enable_server=True,
        milliseconds_wait=500,
        server_address=f"{ARCA_URL}/indices/documents/write?api_key={ARCA_API_KEY}&idx_key={idx_key}",
        max_short_iterations=1,
        max_long_iterations=0,
        json_data=json_data
    )

    if success:
        print("Data posted successfully:", response_text[:500])
    else:
        print("Failed to post data:", response_text)

if __name__ == "__main__":
    test_post_it()