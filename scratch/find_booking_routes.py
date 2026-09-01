import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "/booking" in line or "/confirm_booking" in line or "def dashboard" in line or "def booking" in line:
        print(f"Line {idx}: {line.strip()}")
