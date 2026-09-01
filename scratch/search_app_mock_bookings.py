import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "mock_bookings" in line or "booking_status" in line:
        print(f"Line {idx}: {line.strip()[:110]}")
