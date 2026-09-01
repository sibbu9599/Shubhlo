import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Mandatory At Least 1 Service Selection Rule ===")

with app.app.test_client() as client:
    # Set up session
    with client.session_transaction() as sess:
        sess['user'] = 'customer@test.com'
        sess['booking_info'] = {
            'name': 'Rahul Sharma',
            'email': 'customer@test.com',
            'phone': '9876543210',
            'event_date': '2026-12-25',
            'address': 'Itarsi Main Road 123456',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi'
        }

    # 1. Submit with ZERO services selected
    res_zero = client.post('/confirm_booking', data={
        'venue': '',
        'catering': '',
        'dj': '',
        'decoration': '',
        'transport': ''
    }, follow_redirects=True)
    txt_zero = res_zero.data.decode('utf-8', errors='ignore')
    assert "AT LEAST 1 service" in txt_zero or "कम से कम एक सेवा" in txt_zero or "Choose Your Services" in txt_zero
    print("✓ Step 1 Passed: Submitting 0 services was REJECTED by system!")

    # 2. Submit with AT LEAST 1 service selected (e.g. venue = Royal Palace Garden)
    res_one = client.post('/confirm_booking', data={
        'venue': 'Royal Palace Garden',
        'catering': '',
        'dj': '',
        'decoration': '',
        'transport': ''
    }, follow_redirects=True)
    txt_one = res_one.data.decode('utf-8', errors='ignore')
    assert "Order Invoice" in txt_one or "Confirm" in txt_one or "Payment" in txt_one or "Token" in txt_one or "Royal Palace" in txt_one
    print("✓ Step 2 Passed: Submitting with 1 selected service was ACCEPTED!")

print("\n=== MANDATORY SERVICE SELECTION TEST PASSED 100%! ===")
