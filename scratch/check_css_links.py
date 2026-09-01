import os, re

for root, dirs, files in os.walk('templates'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                css_links = re.findall(r'<link[^>]*href=["\']([^"\']+)["\']', c, re.IGNORECASE)
                print(f'{f:22} -> CSS hrefs: {css_links}')
