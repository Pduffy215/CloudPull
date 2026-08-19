import requests
from Config import ARCA_API_KEY, ARCA_URL

def get_arca_keys(arca_server_url, api_key, namespace, index):

    response = requests.get(f"{arca_server_url}/global_namespaces", params={"api_key": api_key}, timeout=30)
    if not response.ok or not response.text.strip():
        raise RuntimeError(f"Failed to fetch namespaces: status {response.status_code}, body: {response.text[:300]!r}")
    namespaces = response.json()

    ns_key = None
    for name in namespaces:
        if name["name"] == namespace:
            ns_key = name["api_key"]
            break

    if ns_key is None:
        raise RuntimeError(f"Namespace '{namespace}' not found in ARCA")

    response = requests.get(f"{arca_server_url}/indices", params={"api_key": api_key, "ns_key": ns_key}, timeout=30)
    if not response.ok or not response.text.strip():
        raise RuntimeError(f"Failed to fetch indices for namespace '{namespace}': status {response.status_code}, body: {response.text[:300]!r}")
    indices = response.json()

    idx_key = None
    for idx in indices:
        if idx["name"] == index:
            idx_key = idx["api_key"]
            break

    if idx_key is None:
        raise RuntimeError(f"Index '{index}' not found in namespace '{namespace}'")

    return idx_key


def test_get_arca_keys():


    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VIBRATION SPECIALTY CORP", "VSC Default")
    print(idx_key)

if __name__ == "__main__":
    test_get_arca_keys()