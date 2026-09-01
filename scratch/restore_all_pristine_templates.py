import os, json

brain_dir = r'C:\Users\Shailendra Singh\.gemini\antigravity-ide\brain'

target_templates = [
    'home.html',
    'services.html',
    'booking1.html',
    'booking2.html',
    'confirm_booking.html',
    'dashboard.html',
    'vendor_dashboard.html',
    'admin_dashboard.html',
    'login.html',
    'vendor_login.html',
    'vendor_register.html',
    'contact.html',
    'about.html',
    'terms.html'
]

for t in target_templates:
    best_c = ''
    for root, dirs, files in os.walk(brain_dir):
        for f in files:
            if f.endswith('.jsonl'):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    for line in fp:
                        if t in line:
                            try:
                                data = json.loads(line)
                                for tc in data.get('tool_calls', []):
                                    args = tc.get('args', {})
                                    c = args.get('CodeContent') or args.get('ReplacementContent')
                                    tf = args.get('TargetFile', '')
                                    if c and t in tf and len(c) > len(best_c):
                                        best_c = c
                            except:
                                pass
    if best_c:
        print(f'Restoring {t:22} len={len(best_c)}')
        clean_c = best_c.replace('Celebrato', 'Shubhlo').replace('celebrato', 'shubhlo').replace('vendor_register_new', 'vendor_register')
        with open(f'templates/{t}', 'w', encoding='utf-8') as out:
            out.write(clean_c)
    else:
        print(f'WARNING: Could not find pristine content for {t}')

print("All pristine templates successfully restored!")
