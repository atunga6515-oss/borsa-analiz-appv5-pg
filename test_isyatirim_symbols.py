import requests

url = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseOku"
res = requests.get(url)
print(res.text[:200])
