import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from app import app

client = app.test_client()

print("==================================================")
print("TEST: Owner & Admin Dashboard OTP Deal Visibility")
print("==================================================")

with client:
    # Set up session with 1 booking & 1 verified OTP status
    with client.session_transaction() as sess:
        sess['admin'] = 'owner@shubhlo.com'
        sess['is_owner'] = True
        sess['mock_bookings'] = [{
            'id': 401,
            'name': 'Rahul Sharma',
            'phone': '9876543210',
            'email': 'rahul@example.com',
            'event_date': '2026-11-20',
            'amount': 90000.0,
            'token_deposit': 5000.0,
            'status': 'Confirmed',
            'booking_status': 'Confirmed',
            'otp': '948201',
            'is_otp_verified': True,
            'otp_verified': True
        }]
        sess['mock_verifications'] = [{
            'booking_id': 401,
            'vendor_name': 'Royal Palace Lawn',
            'service_type': 'venue',
            'status': 'Verified',
            'verified_at': '2026-08-11 01:15:00'
        }]

    # 1. Test Owner Dashboard
    res_owner = client.get('/owner/dashboard')
    html_owner = res_owner.get_data(as_text=True)

    print("\n1. Owner Dashboard Verification:")
    if '948201' in html_owner and '🎉 Deal Complete (OTP Verified)' in html_owner:
        print("   ✅ SUCCESS: Owner Dashboard shows Security OTP (948201) & Green Deal Complete status! 🎉")
    else:
        print("   ❌ FAIL: Owner Dashboard missing OTP or status.")

    # 2. Test Admin Dashboard
    res_admin = client.get('/admin/dashboard')
    html_admin = res_admin.get_data(as_text=True)

    print("\n2. Admin Dashboard Verification:")
    if '948201' in html_admin and '🎉 Deal Complete (OTP Verified)' in html_admin:
        print("   ✅ SUCCESS: Admin Dashboard shows Security OTP (948201) & Green Deal Complete status! 🎉")
    else:
        print("   ❌ FAIL: Admin Dashboard missing OTP or status.")

print("==================================================")
