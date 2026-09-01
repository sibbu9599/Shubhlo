import os
import re
import glob
from app import app
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))
template_files = glob.glob("templates/**/*.html", recursive=True)

build_errors = []

with app.test_request_context():
    for tpath in template_files:
        rel_path = os.path.relpath(tpath, "templates").replace("\\", "/")
        try:
            with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Find all jinja expressions containing url_for
            url_for_exprs = re.findall(r"url_for\([^)]+\)", content)
            for expr in url_for_exprs:
                # We can evaluate this in Jinja or Python with app's url_for
                # Standardize simple variables for testing
                eval_expr = expr
                # Replace Jinja variables like b.booking_id with dummy values
                eval_expr = re.sub(r"b\.booking_id\s*\|\s*default\([^)]+\)", "1", eval_expr)
                eval_expr = re.sub(r"[a-zA-Z_0-9\.]+(?:\s*\|\s*default\([^)]+\))?", "1", eval_expr)
                # Keep url_for
                eval_expr = re.sub(r"^1\(", "url_for(", eval_expr)
                
                # Check directly in Python
                from flask import url_for
                try:
                    # Parse endpoint name
                    ep_match = re.search(r"url_for\(\s*['\"]([^'\"]+)['\"]", expr)
                    if ep_match:
                        ep = ep_match.group(1)
                        if ep == 'static':
                            continue
                        # Try building url for endpoint
                        rules = [r for r in app.url_map.iter_rules() if r.endpoint == ep]
                        if not rules:
                            build_errors.append((rel_path, expr, f"Endpoint '{ep}' does NOT exist in Flask app!"))
                        else:
                            # Test if rule arguments can be satisfied
                            for r in rules:
                                kwargs = {}
                                for arg in r.arguments:
                                    kwargs[arg] = 1
                                try:
                                    url_for(ep, **kwargs)
                                except Exception as err:
                                    build_errors.append((rel_path, expr, f"Build error for endpoint '{ep}': {err}"))
                except Exception as ex:
                    build_errors.append((rel_path, expr, str(ex)))

        except Exception as e:
            print(f"Error reading {rel_path}: {e}")

print("=== DETAILED BUILD ERROR AUDIT ===")
if not build_errors:
    print("NO BUILD ERRORS DETECTED!")
else:
    for tp, ex, msg in set(build_errors):
        print(f"File: {tp}\n  Expression: {ex}\n  Error: {msg}\n")
