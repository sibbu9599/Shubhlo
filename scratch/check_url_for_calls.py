import re
import glob
from app import app

url_for_pattern = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]([^)]*)\)")

template_files = glob.glob("templates/**/*.html", recursive=True)

endpoints_in_app = set(rule.endpoint for rule in app.url_map.iter_rules())

print(f"Registered endpoints in Flask app ({len(endpoints_in_app)}):")
print(sorted(list(endpoints_in_app)))
print("=" * 60)

errors_found = []

for tpath in template_files:
    with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    matches = url_for_pattern.findall(content)
    for endpoint, args_str in matches:
        # Ignore 'static' which is built-in
        if endpoint not in endpoints_in_app:
            errors_found.append((tpath, endpoint, args_str, "Endpoint NOT registered in Flask app!"))
        else:
            # Check required parameters for endpoint rules
            rules = [r for r in app.url_map.iter_rules() if r.endpoint == endpoint]
            # Check if any rule requires arguments that are missing in args_str
            for r in rules:
                for arg in r.arguments:
                    if arg not in args_str:
                        errors_found.append((tpath, endpoint, args_str, f"Rule {r} requires argument '{arg}' but got args: '{args_str}'"))

print("\n--- URL_FOR AUDIT RESULTS ---")
if not errors_found:
    print("No url_for errors found in templates!")
else:
    for tpath, ep, args, msg in errors_found:
        print(f"File: {tpath}\n  url_for('{ep}'{args})\n  --> {msg}\n")
