import os
from app import app

client = app.test_client()

print("--- Testing all GET endpoints ---")
with app.test_request_context():
    for rule in list(app.url_map.iter_rules()):
        if "GET" in rule.methods and len(rule.arguments) == 0:
            try:
                res = client.get(rule.rule, follow_redirects=True)
                print(f"[OK] {rule.endpoint} -> {rule.rule} (Status: {res.status_code})")
            except Exception as e:
                print(f"[ERROR] {rule.endpoint} -> {rule.rule}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
