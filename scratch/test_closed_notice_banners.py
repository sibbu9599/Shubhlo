import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing System Closed Notice Banners & Form Blocking ===")

with app.app.test_client() as client:
    # Set up Owner Session
    with client.session_transaction() as sess:
        sess['admin'] = 'owner@shubhlo.com'
        sess['is_owner'] = True

    # 1. Turn Customer Booking OFF
    client.post('/owner/toggle_setting', data={'setting_key': 'allow_customer_booking', 'setting_value': 'OFF'})

    with client.session_transaction() as sess:
        sess['user'] = 'customer@test.com'

    res_b1 = client.get('/booking1')
    txt_b1 = res_b1.data.decode('utf-8', errors='ignore')
    assert "Customer Bookings Temporarily Closed" in txt_b1 or "ग्राहक बुकिंग सेवा फ़िलहाल बंद है" in txt_b1
    assert "id=\"bookingForm\"" not in txt_b1
    print("✓ Step 1 Passed: Customer Booking OFF displays closed notice banner and HIDES booking form!")

    # 2. Turn Vendor Registration OFF
    client.post('/owner/toggle_setting', data={'setting_key': 'allow_vendor_registration', 'setting_value': 'OFF'})

    res_vr = client.get('/vendor_register')
    txt_vr = res_vr.data.decode('utf-8', errors='ignore')
    assert "Vendor Registration Temporarily Closed" in txt_vr or "नया वेंडर रजिस्ट्रेशन फ़िलहाल बंद है" in txt_vr
    assert "id=\"vendorRegForm\"" not in txt_vr
    print("✓ Step 2 Passed: Vendor Registration OFF displays closed notice banner and HIDES registration form!")

    # 3. Turn both back ON
    client.post('/owner/toggle_setting', data={'setting_key': 'allow_customer_booking', 'setting_value': 'ON'})
    client.post('/owner/toggle_setting', data={'setting_key': 'allow_vendor_registration', 'setting_value': 'ON'})

    res_b1_on = client.get('/booking1')
    txt_b1_on = res_b1_on.data.decode('utf-8', errors='ignore')
    assert "bookingForm" in txt_b1_on

    res_vr_on = client.get('/vendor_register')
    txt_vr_on = res_vr_on.data.decode('utf-8', errors='ignore')
    assert "vendorRegForm" in txt_vr_on
    print("✓ Step 3 Passed: Turning both back ON restores active forms!")

print("\n=== SYSTEM CLOSED NOTICE BANNERS TEST PASSED 100%! ===")
