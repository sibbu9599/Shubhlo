import re
import glob
from app import app

# Find all rules with parameters
parameterized_rules = {}
for r in app.url_map.iter_rules():
    if r.arguments:
        parameterized_rules[r.endpoint] = list(r.arguments)

print(f"Parameterized endpoints in app ({len(parameterized_rules)}):")
for ep, args in sorted(parameterized_rules.items()):
    print(f"  '{ep}': requires {args}")

print("=" * 60)

all_files = glob.glob("templates/**/*.html", recursive=True) + glob.glob("*.py")

parameter_issues = []

for fpath in all_files:
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Find url_for calls
    matches = re.findall(r"url_for\(\s*['\"]([^'\"]+)['\"]([^)]*)\)", content)
    for ep, args_str in matches:
        if ep in parameterized_rules:
            req_args = parameterized_rules[ep]
            for arg in req_args:
                if arg not in args_str:
                    parameter_issues.append((fpath, ep, req_args, args_str, f"Missing required parameter '{arg}'"))

print("\n=== PARAMETERIZED URL_FOR CALLS AUDIT ===")
if not parameter_issues:
    print("ALL parameterized url_for calls pass their required arguments!")
else:
    for fp, ep, req, got, msg in parameter_issues:
        print(f"File: {fp}\n  url_for('{ep}'{got})\n  --> {msg} (Required: {req})\n")
