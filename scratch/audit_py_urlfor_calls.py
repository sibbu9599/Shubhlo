import re
from app import app
from flask import url_for

with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    code = f.read()

# Find all url_for calls in python code
matches = re.findall(r"url_for\(\s*['\"]([^'\"]+)['\"]([^)]*)\)", code)

endpoints_in_app = set(rule.endpoint for rule in app.url_map.iter_rules())

print(f"Total url_for calls in app.py: {len(matches)}")
print("Auditing python url_for calls...")

py_errors = []

with app.test_request_context():
    for ep, args in matches:
        if ep == 'static':
            continue
        if ep not in endpoints_in_app:
            py_errors.append((ep, args, f"Endpoint '{ep}' NOT in app url_map!"))

print("\n=== PYTHON URL_FOR CALLS AUDIT ===")
if not py_errors:
    print("ALL url_for calls in app.py match valid endpoints!")
else:
    for ep, args, msg in py_errors:
        print(f"  url_for('{ep}'{args}) --> {msg}")
