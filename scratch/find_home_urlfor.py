with open("templates/home.html", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "url_for" in l:
        print(f"Line {i+1}: {l.strip()}")
