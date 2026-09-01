import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("templates/admin_dashboard.html", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i in range(248, min(315, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")
