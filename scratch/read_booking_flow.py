import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

def print_range(start, end):
    print(f"=== LINES {start} to {end} ===")
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}", end="")

print_range(2550, 2750)
