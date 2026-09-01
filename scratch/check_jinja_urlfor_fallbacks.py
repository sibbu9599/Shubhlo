import re
import glob

template_files = glob.glob("templates/**/*.html", recursive=True)

url_for_calls = []

for tpath in template_files:
    with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    matches = re.finditer(r"url_for\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^)]+)\)", content)
    for m in matches:
        ep = m.group(1)
        params_str = m.group(2)
        url_for_calls.append((tpath, ep, params_str))

print(f"Total parameterized url_for calls in templates: {len(url_for_calls)}")
print("=" * 60)
for tp, ep, pstr in url_for_calls:
    print(f"File: {tp}\n  url_for('{ep}', {pstr})")
