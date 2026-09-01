import re
from app import app

with open("app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

route_blocks = []
current_routes = []

for idx, line in enumerate(lines):
    line_str = line.strip()
    if line_str.startswith("@app.route"):
        current_routes.append((idx + 1, line_str))
    elif line_str.startswith("def ") and current_routes:
        func_name = line_str.split("def ")[1].split("(")[0].strip()
        if len(current_routes) > 1:
            route_blocks.append((func_name, current_routes))
        current_routes = []

print(f"Functions with MULTIPLE @app.route decorators ({len(route_blocks)}):")
print("=" * 60)

for func_name, routes in route_blocks:
    print(f"Function '{func_name}':")
    for lnum, rstr in routes:
        print(f"  L{lnum}: {rstr}")
    
    # Test url_for for this endpoint
    with app.test_request_context():
        try:
            url = app.jinja_env.globals['url_for'](func_name)
            print(f"  [OK url_for('{func_name}')] -> {url}")
        except Exception as e:
            print(f"  [BUILDERROR url_for('{func_name}')] -> {e}")
    print("-" * 40)
