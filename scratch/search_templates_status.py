import glob, os, sys
sys.stdout.reconfigure(encoding='utf-8')

for filepath in glob.glob("templates/*.html"):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        if "booking_status" in content or "status-confirmed" in content:
            lines = content.splitlines()
            for idx, line in enumerate(lines, 1):
                if any(k in line for k in ["booking_status", "status-confirmed", "status-pending"]):
                    print(f"{filepath}:{idx}: {line.strip()}")
