import re
import glob
from app import app
from flask import url_for

py_files = glob.glob("**/*.py", recursive=True)
endpoints_in_app = set(rule.endpoint for rule in app.url_map.iter_rules())

py_build_errors = []

with app.test_request_context():
    for ppath in py_files:
        if "venv" in ppath or ".venv" in ppath:
            continue
        with open(ppath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        matches = re.findall(r"url_for\(\s*['\"]([^'\"]+)['\"]([^)]*)\)", content)
        for ep, args_str in matches:
            if ep == 'static':
                continue
            if ep not in endpoints_in_app:
                py_build_errors.append((ppath, ep, args_str, f"Endpoint '{ep}' does NOT exist!"))

print("=== PYTHON FILES URL_FOR AUDIT ===")
if not py_build_errors:
    print("No url_for errors found in Python files!")
else:
    for ppath, ep, args, msg in py_build_errors:
        print(f"File: {ppath}\n  url_for('{ep}'{args})\n  --> {msg}\n")
