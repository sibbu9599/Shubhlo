import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Customer Dashboard & Rate Vendor Endpoint ===")

with app.app.test_client() as client:
    # 1. Login as customer
    with client.session_transaction() as sess:
        sess['user'] = 'customer@test.com'
        sess['user_name'] = 'Rahul Sharma'
        sess['mock_bookings'] = [
            {
                'id': 101,
                'booking_id': 101,
                'name': 'Rahul Sharma',
                'email': 'customer@test.com',
                'phone': '9876543210',
                'event_date': '2026-12-25',
                'venue': 'Royal Palace Garden',
                'catering': 'Shahi Caterers',
                'total_price': 150000,
                'advance_paid': 30000,
                'status': 'Confirmed',
                'invoice_number': 'SHB-2026-101'
            }
        ]

    # 2. Access Customer Dashboard
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 200
    txt_dash = res_dash.data.decode('utf-8', errors='ignore')
    assert "Rate Vendor" in txt_dash or "rate_vendor" in txt_dash or "Invoice" in txt_dash
    print("✓ Step 1 Passed: Customer Dashboard loaded cleanly with zero BuildError!")

    # 3. Access Rate Vendor Page
    res_rate_page = client.get('/rate_vendor?booking_id=101')
    assert res_rate_page.status_code == 200
    print("✓ Step 2 Passed: /rate_vendor page loaded successfully!")

    # 4. Submit Vendor Rating
    res_submit = client.post('/submit_rating', data={
        'booking_id': 101,
        'vendor_name': 'Royal Palace Garden',
        'stars': 5,
        'feedback': 'Excellent venue and arrangement!'
    }, follow_redirects=True)
    assert res_submit.status_code == 200
    print("✓ Step 3 Passed: /submit_rating submitted vendor rating successfully!")

print("\n=== CUSTOMER DASHBOARD & RATING FLOW TEST PASSED 100%! ===")
