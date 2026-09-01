import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "system_settings" in line.lower() or "customer_bookings_enabled" in line.lower() or "vendor_registrations_enabled" in line.lower() or "toggle" in line.lower():
        print(f"Line {idx}: {line.strip()[:110]}")
