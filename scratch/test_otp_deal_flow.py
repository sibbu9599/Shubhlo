import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from app import app

client = app.test_client()

print("==================================================")
print("TEST: Customer OTP & Vendor Deal Completion Flow")
print("==================================================")

with client:
    # 1. Customer session
    with client.session_transaction() as sess:
        sess['user'] = 'customer@example.com'
        sess['user_name'] = 'Customer User'
        sess['mock_bookings'] = [{
            'id': 301,
            'name': 'Customer User',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'event_date': '2026-12-25',
            'amount': 60000.0,
            'status': 'Confirmed',
            'booking_status': 'Confirmed',
            'otp': '784920',
            'venue': 'Royal Palace'
        }]

    # 2. Check Customer Dashboard
    res1 = client.get('/dashboard')
    html1 = res1.get_data(as_text=True)

    print("\n1. Customer Dashboard OTP Card:")
    if '🔑 Deal Completion Security OTP' in html1 and '784920' in html1:
        print("   ✅ SUCCESS: Customer Dashboard displays 6-digit Security OTP (784920)! 🎉")
    else:
        print("   ❌ FAIL: OTP box missing from Customer Dashboard.")

    # 3. Vendor session & verify OTP
    with client.session_transaction() as sess:
        sess['vendor'] = 'vendor@example.com'
        sess['vendor_name'] = 'Royal Palace'
        sess['vendor_service'] = 'venue'

    print("\n2. Vendor Enters Customer OTP (784920):")
    res_verify = client.post('/vendor/verify_otp', data={'booking_id': '301', 'otp': '784920'}, follow_redirects=True)
    v_html = res_verify.get_data(as_text=True)

    if 'OTP Verified Successfully' in v_html:
        print("   ✅ SUCCESS: Vendor OTP verification confirmed deal as SUCCESSFUL! 🎉")
    else:
        print("   ❌ FAIL: OTP verification failed.")

print("==================================================")
