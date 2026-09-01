import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i in range(3328, 3380):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")
