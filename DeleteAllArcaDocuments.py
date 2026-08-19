from Config import ARCA_URL, ARCA_API_KEY, PROJECT_ROOT
from SearchArcaMatch import search_arca_match
from GetArcaKeys import get_arca_keys
import requests
import shutil
import os

def delete_arca_documents(provider, company, site):
        
    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VIBRATION SPECIALTY CORP", "VSC Default")
    data = {
            "partitions":   {"provider_name": provider, "company_name": company, "site_name": site},
        }
    
    documents = search_arca_match(idx_key, data)
    for doc in documents:
        doc_key = doc["api_key"]
        response = requests.get(f"{ARCA_URL}/indices/documents/delete", params= {"api_key": ARCA_API_KEY, "doc_key": doc_key})


    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_DIRECTORY", "Streams_Directory")
    documents = search_arca_match(idx_key, data)
    for doc in documents:
        doc_key = doc["api_key"]
        response = requests.get(f"{ARCA_URL}/indices/documents/delete", params= {"api_key": ARCA_API_KEY, "doc_key": doc_key})


    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_LOG", "Streams_Log")
    documents = search_arca_match(idx_key, data)
    for doc in documents:
        doc_key = doc["api_key"]
        response = requests.get(f"{ARCA_URL}/indices/documents/delete", params= {"api_key": ARCA_API_KEY, "doc_key": doc_key})



if __name__ == "__main__":
    check = input("Are You Sure? ").strip().lower() == "yes"
    if check:

        provider =  "IR PROS"
        company =   "MARIPOSA ENERGY"
        site =      "BYRON CA"

        delete_arca_documents(provider, company, site)