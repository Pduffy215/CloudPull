from platform import machine
from urllib3.util import response
import requests


def get_api_keys(
    protect_server_url,
    company_name,
    provider_name,
    site_name,
    machine_name,
    bearing_name,
    shaft_segment,      # shaft segment ID used to identify the correct bearing when duplicates exist
    start_time          # measurement start time used to match the correct survey
):
    
    site_found = False
    customer_found = False
    provider_found = False
    survey_found = False
    protect_info = {}   # dict that will hold all API keys and type codes
    try:
        # step 1 - get provider key by name from provider list
        response = requests.get(f"{protect_server_url}/provider_list", timeout=30)

        if response.status_code != 200 or not response.text.strip():
            print("Provider list failed")
            return protect_info, provider_found, customer_found, site_found, survey_found

        providers = response.json()
        provider_key = next((p["api_key"] for p in providers if p["name"] == provider_name), None)
        if provider_key == None:
            return protect_info, provider_found, customer_found, site_found, survey_found
        
        provider_found = True
        protect_info["provider_api_key"] = provider_key

        # step 2 - get customer key by company name
        response = requests.get(f"{protect_server_url}/customer_list", params={"api_key": provider_key}, timeout=30)
        customers = response.json()
        customer = next((c for c in customers if c["name"] == company_name), None)
        if customer:
            protect_info["cust_api_key"] = customer["api_key"]
            customer_found = True
        else:
            return protect_info, provider_found, customer_found, site_found, survey_found   # stop early - no point continuing without customer

        # step 3 - get site key by site name under this customer
        response = requests.get(f"{protect_server_url}/site_list_by_customer", params={"api_key": customer["api_key"]}, timeout=30)
        sites = response.json()
        site = next((s for s in sites if s["name"] == site_name), None)
        if site:
            protect_info["site_api_key"] = site["api_key"]
            site_found = True
        else:
            return protect_info, provider_found, customer_found, site_found, survey_found   # stop early - site needs to be created first

        # step 4 - get survey key by matching measurement start date
        response = requests.get(f"{protect_server_url}/survey_list_by_site", params={"api_key": site["api_key"]}, timeout=30)
        surveys = response.json()
        if surveys:
            bearing_date = start_time[:10] if start_time else ""    # extract date portion e.g. "2025-11-24"
            survey = next((s for s in surveys if bearing_date in s["name"]), None)  # find survey matching this date
            if survey is None:
                survey = surveys[0]
                survey_number = int(survey["name"].split()[2].strip(","))   
                print("Survey not found")
                protect_info["survey_number"]  = survey_number
                return protect_info, provider_found, customer_found, site_found, survey_found
            survey_number = int(survey["name"].split()[2].strip(","))   # parse number from "Survey No  2 "
            protect_info["survey_api_key"] = survey["api_key"]
            protect_info["survey_number"]  = survey_number
            survey_found = True
        else:
            print("Survey not found")
            survey_number = 0
            protect_info["survey_number"]  = survey_number
            return protect_info, provider_found, customer_found, site_found, survey_found
        
        # step 5 - get machine key by machine name under this survey
        response = requests.get(f"{protect_server_url}/machine_list_by_survey", params={"api_key": surveys[0]["api_key"]}, timeout=30)
        machines = response.json()
        machine = next((m for m in machines if m["name"] == machine_name), None)
        if machine:
            protect_info["machine_api_key"] = machine["api_key"]
        else:
            return protect_info, provider_found, customer_found, site_found, survey_found

        # step 6 - get component (bearing) key by bearing name and shaft segment
        response = requests.get(f"{protect_server_url}/component_list_by_machine", params={"survey_key": surveys[0]["api_key"], "machine_key": machine["api_key"] if machine else None}, timeout=30)
        bearings = response.json()
        bearing = next((b for b in bearings if b["description"] == bearing_name and b["shaft_id"] == str(shaft_segment)), None)  # match by name AND shaft to avoid duplicates
        if bearing:
            protect_info["component_api_key"] = bearing["api_key"]
        else:
            print("Bearing not found:", bearing_name, "shaft segment:", shaft_segment)
            return protect_info, provider_found, customer_found, site_found, survey_found

        # step 7 - get signal key and type codes from full machine JSON
        response = requests.get(f"{protect_server_url}/machine_by_key", params={"api_key": machine["api_key"] if bearing else None}, timeout=30)
        machine_data = response.json()
        components = machine_data["machine"]["components"]
        component = next((c for c in components                         # find component matching bearing name and shaft
                        if c["componentDescription"] == bearing_name 
                        and c["shaft_id"] == str(shaft_segment)), None)
        if component:
            signals = component.get("signals", [])
            if signals:
                signal = signals[0]     # all signals named Triax so just take first
                protect_info["signal_api_key"] = signal["signalId"]

                # extract type codes from signal metadata - used for equip_type/shaft_type/brg_type in JSON
                meta = signal["signalMetaData"]["component Levels"]
                protect_info["brg_type"]   = f"{meta['Bearing']['sg_type_db_site']};{meta['Bearing']['sg_type_db_id']};{meta['Bearing']['sg_type_code']}"
                protect_info["equip_type"] = f"{meta['Equipment']['sg_type_db_site']};{meta['Equipment']['sg_type_db_id']};{meta['Equipment']['sg_type_code']}"
                protect_info["shaft_type"] = f"{meta['Shaft']['sg_type_db_site']};{meta['Shaft']['sg_type_db_id']};{meta['Shaft']['sg_type_code']}"

    except Exception as e:
        print(f"Error: {e}")   # catch any network or parsing errors without crashing

    return protect_info, provider_found, customer_found, site_found, survey_found   # True = site exists and keys were retrieved


def test_get_site_found():
    protect_info, provider_found, customer_found, site_found, survey_found = get_api_keys(
        protect_server_url = "http://vscprotect.twintechlabs.io",
        provider_name      = "VSC_DEV4",
        company_name       = "Test Company",
        site_name          = "Test Site_metadata",
        machine_name       = "C-1",
        bearing_name       = "BOTTOM BRG",
        shaft_segment      = "15",          
        start_time         = "2025-11-24 12:00:00"
    )
    print("Retrieved API protect_info:", protect_info)
    print("Provider found:", provider_found)
    print("Customer found:", customer_found)
    print("Site found:", site_found)
    print("Survey found:", survey_found)

if __name__ == "__main__":
    test_get_site_found()
    