import requests

url = "https://www.kap.org.tr/tr/api/memberEntities"
res = requests.get(url)
data = res.json()
bist_stocks = [m for m in data if m.get('isBist')]
print(f"Total members: {len(data)}, BIST members: {len(bist_stocks)}")
if bist_stocks:
    print("Sample:", bist_stocks[0:3])
