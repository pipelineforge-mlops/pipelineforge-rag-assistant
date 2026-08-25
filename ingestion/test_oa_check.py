import requests

pmc_ids = ['13477411', '13477267', '13477211', '13477233', '13477176']

for pid in pmc_ids:
    full_id = f"PMC{pid}"
    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={full_id}"
    response = requests.get(url)
    print(f"--- {full_id} ---")
    print(response.text[:500])
    print()