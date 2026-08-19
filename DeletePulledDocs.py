from Config import ARCA_URL, ARCA_API_KEY
from SearchArcaMatch import search_arca_match
from GetArcaKeys import get_arca_keys
import requests
import shutil
import os

def delete_pulled_docs(provider, company, site):
        
    data = {
            "partitions":   {"provider_name": provider, "company_name": company, "site_name": site},
            "indices"   :   {"posted_or_pulled?": "Pulled"}
        }

    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_LOG", "Streams_Log")
    documents = search_arca_match(idx_key, data)
    for doc in documents:
        doc_key = doc["api_key"]
        response = requests.get(f"{ARCA_URL}/indices/documents/delete", params= {"api_key": ARCA_API_KEY, "doc_key": doc_key})

    output_folder = f"Pulled Streams/{data['partitions']['company_name']} Pulled"
    output_path = f"{os.path.dirname(os.path.abspath(__file__))}/{output_folder}"
    shutil.rmtree(output_path)


if __name__ == "__main__":
    check = input("Are You Sure? ").strip().lower() == "yes"
    if check:

        provider =  "FREIJE"
        company =   "WALMART DC 6858"
        site =      "MEBANE NC"


        delete_pulled_docs(provider, company, site)