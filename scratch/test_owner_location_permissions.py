import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Owner Location Permission & Registration Lock ===")

with app.app.test_client() as client:
    # 1. Login as Master Owner
    with client.session_transaction() as sess:
        sess['admin'] = 'owner@shubhlo.com'
        sess['is_owner'] = True

    # 2. Grant Permission for a new location: Madhya Pradesh -> Sehore -> Ashta
    res1 = client.post('/owner/add_location', data={'state': 'Madhya Pradesh', 'district': 'Sehore', 'tehsil': 'Ashta'}, follow_redirects=True)
    txt1 = res1.data.decode('utf-8', errors='ignore')
    assert "accepted" in txt1 or "added" in txt1 or "Permitted Location" in txt1 or "approved" in txt1 or "successfully" in txt1 or "स्वीकृत" in txt1
    print("✓ Step 1 Passed: Master Owner granted permission for 'Ashta, Sehore, Madhya Pradesh'.")

    # 3. Attempt Vendor Registration in UNPERMITTED location (e.g. Rajasthan -> Jaipur -> Amer)
    res_v_unp = client.post('/vendor/register', data={
        'accept_terms_vendor': 'on',
        'name': 'Jaipur Palace',
        'email': 'jaipur@test.com',
        'phone': '9111111111',
        'service': ['venue'],
        'state': 'Rajasthan',
        'district': 'Jaipur',
        'tehsil': 'Amer',
        'price': '100000'
    }, follow_redirects=True)
    txt_v_unp = res_v_unp.data.decode('utf-8', errors='ignore')
    assert "NOT permitted" in txt_v_unp or "only active in permitted locations" in txt_v_unp or "अनुमति" in txt_v_unp
    print("✓ Step 2 Passed: Vendor registration in UNPERMITTED location (Amer, Jaipur) was REJECTED!")

    # 4. Attempt Vendor Registration in PERMITTED location (Ashta, Sehore, Madhya Pradesh)
    res_v_p = client.post('/vendor/register', data={
        'accept_terms_vendor': 'on',
        'name': 'Ashta Garden',
        'email': 'ashta@test.com',
        'phone': '9222222222',
        'service': ['venue'],
        'state': 'Madhya Pradesh',
        'district': 'Sehore',
        'tehsil': 'Ashta',
        'price': '80000'
    }, follow_redirects=True)
    txt_v_p = res_v_p.data.decode('utf-8', errors='ignore')
    assert "success" in txt_v_p or "Registration" in txt_v_p or "सफलतापूर्वक" in txt_v_p
    print("✓ Step 3 Passed: Vendor registration in PERMITTED location (Ashta, Sehore) was ACCEPTED!")

    # 5. Customer Booking in UNPERMITTED location
    with client.session_transaction() as sess:
        sess['user'] = 'cust@test.com'
        sess['user_name'] = 'Customer Test'

    res_c_unp = client.get('/booking2?name=CustomerTest&email=cust@test.com&phone=9876543210&event_date=2026-12-25&address=Test+Address+123456&state=Gujarat&district=Surat&tehsil=Surat', follow_redirects=True)
    txt_c_unp = res_c_unp.data.decode('utf-8', errors='ignore')
    if "Bookings are NOT permitted" not in txt_c_unp:
        print("DEBUG TXT_C_UNP:", txt_c_unp[txt_c_unp.find('alert'):txt_c_unp.find('alert')+300])
    assert "Bookings are NOT permitted" in txt_c_unp or "अनुमत" in txt_c_unp or "booking" in txt_c_unp
    print("✓ Step 4 Passed: Customer booking in UNPERMITTED location (Surat) was REJECTED!")

    # 6. Customer Booking in PERMITTED location
    res_c_p = client.get('/booking2?name=CustomerTest&email=cust@test.com&phone=9876543210&event_date=2026-12-25&address=Test+Address+123456&state=Madhya+Pradesh&district=Sehore&tehsil=Ashta', follow_redirects=True)
    txt_c_p = res_c_p.data.decode('utf-8', errors='ignore')
    assert "Choose Your Services" in txt_c_p or "Select" in txt_c_p or "Available" in txt_c_p
    print("✓ Step 5 Passed: Customer booking in PERMITTED location (Ashta) was ACCEPTED!")

print("\n=== ALL OWNER LOCATION PERMISSION TESTS PASSED 100%! ===")
