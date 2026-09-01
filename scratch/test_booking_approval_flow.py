import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from app import app

client = app.test_client()

print("==================================================")
print("TEST: Booking Approval & Customer Dashboard Flow")
print("==================================================")

with client:
    with client.session_transaction() as sess:
        sess['user'] = 'customer@example.com'
        sess['user_name'] = 'Customer User'
        sess['mock_bookings'] = [{
            'id': 201,
            'name': 'Customer User',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Main St',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'event_date': '2026-12-25',
            'amount': 50000.0,
            'token_deposit': 5000.0,
            'payment_status': 'Paid',
            'payment_method': 'UPI',
            'status': 'Pending Admin Approval',
            'booking_status': 'Pending Admin Approval',
            'venue': 'Royal Palace'
        }]

    # 1. Access Dashboard BEFORE Approval
    res1 = client.get('/dashboard')
    html1 = res1.get_data(as_text=True)

    print("\n1. Customer Dashboard BEFORE Approval:")
    if '<span class="status-badge status-pending">' in html1 and "Pending Admin Approval" in html1:
        print("   ✅ SUCCESS: Badge is yellow pending ('⏳ Pending Admin Approval').")
    else:
        print("   ❌ FAIL: Pending badge missing.")

    if '<span class="status-badge status-confirmed">' in html1:
        print("   ❌ FAIL: Badge prematurely showed 'Confirmed'.")
    else:
        print("   ✅ SUCCESS: Confirmed badge is NOT present before approval.")

    # 2. Admin approves booking #201
    with client.session_transaction() as sess:
        sess['admin'] = True

    print("\n2. Admin Approves Booking #201:")
    res_approve = client.post('/admin/approve_booking/201', follow_redirects=True)
    print(f"   Response Code: {res_approve.status_code}")

    # 3. Access Dashboard AFTER Admin Approval
    res2 = client.get('/dashboard')
    html2 = res2.get_data(as_text=True)

    print("\n3. Customer Dashboard AFTER Approval:")
    if '<span class="status-badge status-confirmed">' in html2 and "✔ Confirmed / पुष्ट की गई" in html2:
        print("   ✅ SUCCESS: Badge updated to green confirmed ('✔ Confirmed / पुष्ट की गई') after Admin approval! 🎉")
    else:
        print("   ❌ FAIL: Badge did not update to confirmed.")
print("==================================================")
