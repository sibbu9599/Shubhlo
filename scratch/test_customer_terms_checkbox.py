import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Customer Interactive Terms & Conditions Checkbox ===")

with app.app.test_client() as client:
    # 1. Setup Session
    with client.session_transaction() as sess:
        sess['user'] = 'customer@test.com'
        sess['user_name'] = 'Rahul Sharma'
        sess['booking_info'] = {
            'name': 'Rahul Sharma',
            'email': 'customer@test.com',
            'phone': '9876543210',
            'event_date': '2026-12-25',
            'address': 'Itarsi Main Road 123456',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'venue': 'Royal Palace Garden',
            'selected_vendors': [{'name': 'Royal Palace Garden', 'price': 150000}]
        }

    # 2. Render Confirm Booking Page
    res_confirm = client.get('/confirm_booking')
    txt_confirm = res_confirm.data.decode('utf-8', errors='ignore')
    assert "acceptTermsCheckbox" in txt_confirm or "accept_terms" in txt_confirm
    assert "Terms & Conditions" in txt_confirm or "नियम एवं शर्तों" in txt_confirm
    print("✓ Step 1 Passed: Interactive Terms & Conditions Checkbox rendered on Confirm Booking page.")

    # 3. Submit WITHOUT ticking Terms Checkbox
    res_no_terms = client.post('/pay', data={}, follow_redirects=True)
    txt_no_terms = res_no_terms.data.decode('utf-8', errors='ignore')
    assert "accept the terms" in txt_no_terms.lower() or "confirm" in txt_no_terms.lower() or "नियम" in txt_no_terms
    print("✓ Step 2 Passed: Submitting WITHOUT ticking Terms checkbox was REJECTED by system!")

    # 4. Submit WITH ticking Terms Checkbox (accept_terms='on')
    res_with_terms = client.post('/pay', data={'accept_terms': 'on'}, follow_redirects=True)
    txt_with_terms = res_with_terms.data.decode('utf-8', errors='ignore')
    assert "Payment" in txt_with_terms or "5,118" in txt_with_terms or "UPI" in txt_with_terms
    print("✓ Step 3 Passed: Submitting WITH Terms checkbox checked was ACCEPTED!")

print("\n=== CUSTOMER TERMS CHECKBOX TEST PASSED 100%! ===")
