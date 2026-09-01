with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if l.strip().startswith("def "):
        func = l.split("def ")[1].split("(")[0].strip()
        if "booking" in func or "index" in func:
            print(f"Line {i+1}: def {func}")
