import os
import re
import glob
from app import app

# Gather all valid rules in Flask app
valid_rules = set()
for r in app.url_map.iter_rules():
    rule_str = r.rule
    # Normalize rules
    valid_rules.add(rule_str)
    # Also add standard endpoints without leading slash
    valid_rules.add(rule_str.lstrip("/"))

print("Valid Flask rules:")
print(sorted(list(valid_rules)))
print("=" * 60)

link_patterns = [
    re.compile(r'href=["\']([^"\']+)["\']'),
    re.compile(r'action=["\']([^"\']+)["\']'),
    re.compile(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'redirect\s*\(\s*["\']([^"\']+)["\']')
]

all_files = glob.glob("templates/**/*.html", recursive=True) + glob.glob("static/**/*.js", recursive=True) + glob.glob("*.py")

suspicious_links = []

for filepath in all_files:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    for pattern in link_patterns:
        for match in pattern.findall(content):
            link = match.strip()
            # Ignore external links, mailto, tel, javascript, dynamic jinja tags
            if link.startswith(('http://', 'https://', 'mailto:', 'tel:', '#', 'javascript:', '{{', '{%')):
                continue
            if not link:
                continue

            # Strip query string or anchor
            clean_link = link.split('?')[0].split('#')[0]

            # Check if clean_link matches any Flask rule
            matched = False
            for rule in valid_rules:
                if clean_link == rule or clean_link == '/' + rule or clean_link == rule + '/' or clean_link == '/' + rule + '/':
                    matched = True
                    break
                # Simple parameter match e.g. /booking/receipt/1
                if '<' in rule:
                    regex_rule = re.sub(r'<[^>]+>', r'[^/]+', rule)
                    if re.fullmatch(regex_rule, clean_link) or re.fullmatch(regex_rule, '/' + clean_link):
                        matched = True
                        break

            if not matched:
                suspicious_links.append((filepath, link))

print("=== 404 LINK AUDIT RESULTS ===")
if not suspicious_links:
    print("No 404 links found!")
else:
    for fp, link in set(suspicious_links):
        print(f"File: {fp}  --> Broken Link: '{link}'")
