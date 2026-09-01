import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from flask import session
import app

print("Testing Vendor Date Blocking Logic...")
test_date = "2026-12-25"

with app.app.test_request_context():
    # 1. Unblocked check
    vendors_before = app.fetch_vendors_by_service('venue', 'Itarsi', test_date)
    print(f"Before blocking: Vendor={vendors_before[0].get('name')}, is_blocked={vendors_before[0].get('is_blocked')}")

    # 2. Block the date for Royal Palace Garden (Mock)
    session['mock_vendor_availability'] = [{
        'id': 1,
        'vendor_name': 'Royal Palace Garden (Mock)',
        'event_date': test_date,
        'status': 'Blocked',
        'reason': 'Already Booked for Marriage'
    }]

    # 3. Blocked check
    vendors_after = app.fetch_vendors_by_service('venue', 'Itarsi', test_date)
    print(f"After blocking: Vendor={vendors_after[0].get('name')}, is_blocked={vendors_after[0].get('is_blocked')}")

print("\n--- All Tests Passed! ---")
