with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "/booking" in l or "booking" in l:
        if "@app.route" in l or "def " in l:
            print(f"Line {i+1}: {l.strip()}")
