import sys
from top_picks_15d import get_top_picks_15d
res = get_top_picks_15d(10, ["BIST 30"])
for item in res:
    print(f"{item['ticker']}: Score {item['score']}, Summary:\n{item['summary']}\n")
