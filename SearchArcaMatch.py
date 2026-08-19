import requests
from GetArcaKeys import get_arca_keys
from Config import ARCA_URL, ARCA_API_KEY
import json


def search_arca_match(idx_key, data):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = requests.post(f"{ARCA_URL}/indices/documents/match", params={"api_key": ARCA_API_KEY, "idx_key": idx_key}, json=data, headers=headers, timeout=30)

    if not response.ok:
        print(f"ARCA search failed — status {response.status_code}: {response.text[:300]}")
        return []

    if not response.text.strip():
        return []  # server returned success with no body — treat as no matches

    return response.json()


def test_search_arca_match():

    provider = "FREIJE"
    company = "WALMART DC 6858"
    site =    "MEBANE NC"
    
    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_LOG", "Streams_Log")
    data = {
                "partitions": {"provider_name": "FREIJE", "company_name": "WALMART DC 6858", "site_name": "MEBANE NC"},
                "indices": {"survey_no": "1", "posted_or_pulled?": "Posted"},
            }
            
    result = search_arca_match(idx_key, data)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_search_arca_match()
   