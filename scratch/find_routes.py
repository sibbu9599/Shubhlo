with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

keywords = ["booking_status", "def dashboard", "approve", "booking2", "payment_status", "Pending", "Confirmed"]

for idx, line in enumerate(lines, 1):
    for kw in keywords:
        if kw.lower() in line.lower():
            print(f"Line {idx}: [{kw}] {line.strip()[:100]}")
            break
