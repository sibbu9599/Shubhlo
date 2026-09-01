import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("templates/admin_dashboard.html", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "approve" in line.lower() or "booking" in line.lower() or "pending" in line.lower():
        print(f"Line {idx}: {line.strip()[:110]}")
