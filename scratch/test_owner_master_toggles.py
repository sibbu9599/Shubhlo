import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Owner Master ON/OFF Controls Switchboard ===")

with app.app.test_client() as client:
    # Set up Owner Session
    with client.session_transaction() as sess:
        sess['admin'] = 'owner@shubhlo.com'
        sess['is_owner'] = True

    # 1. Owner Turns Customer Booking OFF
    res_off1 = client.post('/owner/toggle_setting', data={
        'setting_key': 'allow_customer_booking',
        'setting_value': 'OFF'
    }, follow_redirects=True)
    assert res_off1.status_code == 200
    print("✓ Step 1 Passed: Owner turned Customer Booking OFF!")

    # Verify Customer Booking is blocked
    val, msg = app.get_system_setting('allow_customer_booking')
    assert val == 'OFF'
    print("✓ Step 2 Passed: get_system_setting('allow_customer_booking') returns OFF!")

    # 2. Owner Turns Customer Booking ON
    res_on1 = client.post('/owner/toggle_setting', data={
        'setting_key': 'allow_customer_booking',
        'setting_value': 'ON'
    }, follow_redirects=True)
    assert res_on1.status_code == 200
    val_on, _ = app.get_system_setting('allow_customer_booking')
    assert val_on == 'ON'
    print("✓ Step 3 Passed: Owner turned Customer Booking ON!")

    # 3. Owner Turns Vendor Registration OFF
    res_off2 = client.post('/owner/toggle_setting', data={
        'setting_key': 'allow_vendor_registration',
        'setting_value': 'OFF'
    }, follow_redirects=True)
    assert res_off2.status_code == 200
    val_v, _ = app.get_system_setting('allow_vendor_registration')
    assert val_v == 'OFF'
    print("✓ Step 4 Passed: Owner turned Vendor Registration OFF!")

    # 4. Owner Turns Vendor Registration ON
    res_on2 = client.post('/owner/toggle_setting', data={
        'setting_key': 'allow_vendor_registration',
        'setting_value': 'ON'
    }, follow_redirects=True)
    assert res_on2.status_code == 200
    val_v_on, _ = app.get_system_setting('allow_vendor_registration')
    assert val_v_on == 'ON'
    print("✓ Step 5 Passed: Owner turned Vendor Registration ON!")

print("\n=== ALL OWNER MASTER TOGGLE TESTS PASSED 100%! ===")
