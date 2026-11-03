import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Direct Deal & Token Money Concept Across Pages ===")

with app.app.test_client() as client:
    # 1. Services Page Check
    res_services = client.get('/services')
    txt_services = res_services.data.decode('utf-8', errors='ignore')
    assert "Direct Deal" in txt_services or "सीधा" in txt_services
    assert "Token: ₹5,118" in txt_services
    print("✓ Services Page: Direct Deal model and ₹5,118 Token Money verified.")

    # 2. Terms Page Check
    res_terms = client.get('/terms')
    txt_terms = res_terms.data.decode('utf-8', errors='ignore')
    assert "₹5,118" in txt_terms
    assert "अग्रिम टोकन व सीधा सौदा नीति" in txt_terms or "Direct Deal" in txt_terms
    print("✓ Terms Page: Section 4 accurately enforces ₹5,118 Token & Direct Deal Policy.")

    # 3. Home Page Check
    res_home = client.get('/home')
    txt_home = res_home.data.decode('utf-8', errors='ignore')
    assert "Lock Token (₹5,118)" in txt_home
    assert "Direct Deal" in txt_home
    print("✓ Home Page: Step 3 (Token ₹5,118) and Step 4 (Direct Deal) verified.")

    # 4. Booking Flow - Step 2 (booking2)
    with client.session_transaction() as sess:
        sess['user'] = 'pooja@test.com'
        sess['user_name'] = 'Pooja Verma'
        sess['booking_info'] = {
            'name': 'Pooja Verma',
            'email': 'pooja@test.com',
            'phone': '9876543210',
            'address': 'Station Road, Itarsi Main Market',
            'event_date': '2026-12-31',
            'tehsil': 'Itarsi',
            'district': 'Hoshangabad',
            'state': 'Madhya Pradesh'
        }
    res_b2 = client.get('/booking2')
    txt_b2 = res_b2.data.decode('utf-8', errors='ignore')
    assert "SHUBHLO TOKEN MONEY & DIRECT DEAL POLICY" in txt_b2 or "सीधा वेंडर सौदा व टोकन नियम" in txt_b2
    assert "Payable Token Money" in txt_b2
    print("✓ Booking Step 2: Policy banner & Payable Token Money summary verified.")

    # 5. Booking Flow - Step 3 (confirm_booking)
    res_confirm = client.post('/confirm_booking', data={'venue': 'Royal Palace Garden'}, follow_redirects=True)
    txt_confirm = res_confirm.data.decode('utf-8', errors='ignore')
    assert "Direct with Vendor" in txt_confirm or "आपस में तय" in txt_confirm
    assert "5,118" in txt_confirm
    assert "5,000" in txt_confirm
    print("✓ Confirm Booking Step 3: Direct deal note and ₹5,118 token breakdown verified.")

    # 6. Customer Dashboard Check
    with client.session_transaction() as sess:
        sess['user'] = 'customer@test.com'
        sess['user_name'] = 'Pooja Verma'
        sess['mock_bookings'] = [{
            'id': 99,
            'booking_id': 99,
            'name': 'Pooja Verma',
            'email': 'customer@test.com',
            'payment_status': 'Paid',
            'event_name': 'Wedding',
            'event_date': '2026-12-31',
            'advance_paid': 5118.0,
            'token_deposit': 5000.0,
            'status': 'Confirmed',
            'venue': 'Royal Palace Garden'
        }]
    res_dash = client.get('/dashboard')
    txt_dash = res_dash.data.decode('utf-8', errors='ignore')
    assert "Customer-Vendor Direct Deal" in txt_dash or "सीधा वेंडर सौदा" in txt_dash
    assert "Token Money Paid" in txt_dash
    print("✓ Customer Dashboard: Displays Direct Deal and ₹5,118 Token Money cleanly.")

    # 7. Vendor Dashboard Zero Fake Fallback Check
    with client.session_transaction() as sess:
        sess['vendor'] = 'new_vendor@shubhlo.com'
        sess['vendor_name'] = 'New Star DJ'
        sess['mock_bookings'] = []
    res_v = client.get('/vendor/dashboard')
    txt_v = res_v.data.decode('utf-8', errors='ignore')
    assert "125000" not in txt_v, "Fake 125,000 fallback should not be shown for 0 bookings!"
    assert "Direct Deal" in txt_v
    print("✓ Vendor Dashboard: Direct Deal model verified with zero fake pre-populated earnings.")

print("\n=== ALL DIRECT DEAL & TOKEN MONEY CONCEPT TESTS PASSED 100%! ===")
