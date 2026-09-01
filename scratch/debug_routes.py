import sys
sys.path.insert(0, '.')
from app import app
from flask import url_for

print("Iterating rules in app.url_map:")
for r in app.url_map.iter_rules():
    if "booking" in r.endpoint:
        print(f"Rule: {r.rule} -> endpoint: {r.endpoint}")

with app.test_request_context():
    try:
        u1 = url_for('booking1')
        print("SUCCESS url_for('booking1'):", u1)
    except Exception as e:
        print("FAILED url_for('booking1'):", type(e), e)

    try:
        u2 = url_for('booking')
        print("SUCCESS url_for('booking'):", u2)
    except Exception as e:
        print("FAILED url_for('booking'):", type(e), e)
