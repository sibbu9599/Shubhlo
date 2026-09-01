import re
import glob
from app import app

all_files = glob.glob("templates/**/*.html", recursive=True) + glob.glob("static/**/*.js", recursive=True)

endpoints_in_app = set(rule.endpoint for rule in app.url_map.iter_rules())

script_url_for_errors = []

for fpath in all_files:
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Find url_for calls in JS or Jinja script blocks
    matches = re.findall(r"url_for\(\s*['\"]([^'\"]+)['\"]([^)]*)\)", content)
    for ep, args in matches:
        if ep == 'static':
            continue
        if ep not in endpoints_in_app:
            script_url_for_errors.append((fpath, ep, args))

print("=== ALL FILES URL_FOR ENDPOINT MATCH AUDIT ===")
if not script_url_for_errors:
    print("NO UNREGISTERED ENDPOINTS FOUND IN ANY FILE!")
else:
    for fp, ep, args in script_url_for_errors:
        print(f"File: {fp}\n  url_for('{ep}'{args})\n")
