import re
import glob

files = [
    "frontend/src/app/screener/page.tsx",
    "frontend/src/app/top-picks/page.tsx",
    "frontend/src/app/top-picks-15d/page.tsx",
    "frontend/src/app/alpharank/page.tsx"
]

for file in files:
    with open(file, "r") as f:
        content = f.read()

    # Remove `const { addTicker } = useWatchlist();`
    content = re.sub(r'^\s*const { addTicker } = useWatchlist\(\);\n', '', content, flags=re.MULTILINE)

    # Remove the button block
    button_regex = r'<button[^>]*onClick=\{\(\)\s*=>\s*addTicker\([^)]*\)\}[^>]*>.*?<\/button>'
    content = re.sub(button_regex, '', content, flags=re.DOTALL)

    with open(file, "w") as f:
        f.write(content)

print("Pruned addTicker and buttons")
