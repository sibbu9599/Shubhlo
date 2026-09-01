from app import app

print("=== ALL REGISTERED FLASK ENDPOINTS ===")
for rule in app.url_map.iter_rules():
    print(f"Endpoint: {rule.endpoint:30s} -> Rule: {rule.rule}")

print("\nTesting url_for('booking1')...")
with app.test_request_context():
    from flask import url_for
    try:
        url = url_for('booking1')
        print(f"SUCCESS: url_for('booking1') = {url}")
    except Exception as e:
        print(f"ERROR: url_for('booking1') failed with: {e}")
