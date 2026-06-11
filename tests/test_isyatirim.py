import requests

url = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseOku"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers)
try:
    data = res.json()
    print("Total symbols:", len(data))
    if len(data) > 0:
        print("Sample:", data[0])
except Exception as e:
    print("Error:", e, res.text[:100])
