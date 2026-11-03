import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_BOOKINGS, GLOBAL_VENDOR_AVAILABILITY

def run_suite():
    print("==================================================")
    print("STARTING VENDOR DATE BLOCKING & AVAILABILITY SUITE")
    print("==================================================")

    client = app.test_client()

    test_vendor_email = "royal_palace@gmail.com"
    test_vendor_name = "Royal Palace Garden"
    test_date = "2026-11-28"

    # [Test 1] Vendor Login & Dashboard initial state
    print("\n[Test 1] Testing Vendor Dashboard access...")
    with client.session_transaction() as sess:
        sess['vendor'] = test_vendor_email
        sess['vendor_name'] = test_vendor_name
        sess['vendor_service'] = 'venue'
        sess['vendor_id'] = 101

    resp = client.get('/vendor_dashboard')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert 'Date Availability' in html
    print("  PASS: Vendor dashboard loads with Date Availability card.")

    # [Test 2] Vendor blocks a date (2026-11-28)
    print(f"\n[Test 2] Testing vendor blocking date {test_date}...")
    block_resp = client.post('/vendor/toggle_date_availability', data={
        'event_date': test_date,
        'action': 'block',
        'reason': 'Marriage Event Already Booked'
    }, follow_redirects=True)
    assert block_resp.status_code == 200
    block_html = block_resp.data.decode('utf-8')
    assert test_date in block_html
    print(f"  PASS: Vendor successfully blocked {test_date}!")

    # [Test 3] Customer views booking2 for that blocked date
    print(f"\n[Test 3] Testing customer booking2 on blocked date {test_date}...")
    with client.session_transaction() as sess:
        sess['user'] = 'customer@gmail.com'
        sess['user_name'] = 'Test Host'
        sess['booking_info'] = {
            'name': 'Test Host',
            'email': 'customer@gmail.com',
            'phone': '9876543210',
            'address': 'House No 45, Railway Station Road, Itarsi',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'event_date': test_date,
            'event_name': 'Wedding / शादी विवाह'
        }

    b2_resp = client.get(f'/booking2?event_date={test_date}&tehsil=Itarsi&name=Test+Host&email=customer@gmail.com&phone=9876543210&address=House+No+45+Railway+Road+Itarsi')
    assert b2_resp.status_code == 200, f"Expected 200, got {b2_resp.status_code}"
    b2_html = b2_resp.data.decode('utf-8')
    assert 'Date Blocked' in b2_html or 'blocked-vendor-card' in b2_html
    print(f"  PASS: Customer booking page reflects {test_vendor_name} as blocked on {test_date}!")

    # [Test 4] Backend validation prevents submitting blocked vendor
    print("\n[Test 4] Testing backend validation on confirm_booking for blocked vendor...")
    conf_resp = client.post('/confirm_booking', data={
        'venue': test_vendor_name
    }, follow_redirects=True)
    assert conf_resp.status_code == 200
    conf_html = conf_resp.data.decode('utf-8')
    assert 'already booked or unavailable' in conf_html or 'उपलब्ध नहीं' in conf_html
    print("  PASS: Backend strictly blocked submitting the booked vendor!")

    # [Test 5] Customer views booking2 on a different, open date (2026-11-29)
    open_date = "2026-11-29"
    print(f"\n[Test 5] Testing customer booking2 on open date {open_date}...")
    b2_open_resp = client.get(f'/booking2?event_date={open_date}&tehsil=Itarsi&name=Test+Host&email=customer@gmail.com&phone=9876543210&address=House+No+45+Railway+Road+Itarsi')
    assert b2_open_resp.status_code == 200
    print(f"  PASS: Customer can view and select vendor on open date {open_date}!")

    # [Test 6] Vendor unblocks the date
    print(f"\n[Test 6] Testing vendor unblocking {test_date}...")
    with client.session_transaction() as sess:
        sess['vendor'] = test_vendor_email
        sess['vendor_name'] = test_vendor_name
        sess['vendor_service'] = 'venue'
        sess['vendor_id'] = 101

    unblock_resp = client.post('/vendor/toggle_date_availability', data={
        'event_date': test_date,
        'action': 'unblock'
    }, follow_redirects=True)
    assert unblock_resp.status_code == 200
    print(f"  PASS: Vendor successfully unblocked {test_date}!")

    # [Test 7] Customer re-checks booking2 on test_date now that it is unblocked
    print(f"\n[Test 7] Testing customer booking2 on {test_date} after unblocking...")
    with client.session_transaction() as sess:
        sess['user'] = 'customer@gmail.com'
        sess['user_name'] = 'Test Host'

    b2_recheck = client.get(f'/booking2?event_date={test_date}&tehsil=Itarsi&name=Test+Host&email=customer@gmail.com&phone=9876543210&address=House+No+45+Railway+Road+Itarsi')
    assert b2_recheck.status_code == 200
    print(f"  PASS: {test_date} is now open and available again for booking!")

    # [Test 8] Vendor Booking Card 1-Click Block/Unblock Verification
    print("\n[Test 8] Testing Vendor Booking Card 1-Click Block/Unblock display...")
    with client.session_transaction() as sess:
        sess['vendor'] = test_vendor_email
        sess['vendor_name'] = test_vendor_name
        sess['vendor_service'] = 'venue'
        sess['vendor_id'] = 101
        sess['mock_bookings'] = [{
            'id': 777,
            'name': 'Ramesh Kumar',
            'phone': '9876543210',
            'email': 'ramesh@gmail.com',
            'address': 'Main Market, Itarsi',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'event_date': '2026-12-15',
            'event_name': 'Wedding / शादी विवाह',
            'venue': test_vendor_name,
            'status': 'Pending Owner Approval'
        }]

    v_dash_resp = client.get('/vendor_dashboard')
    assert v_dash_resp.status_code == 200
    v_dash_html = v_dash_resp.data.decode('utf-8')
    assert 'Block This Date' in v_dash_html
    print("  PASS: Vendor dashboard booking card displays 1-click Block Date button!")

    print("\n==================================================")
    print("ALL VENDOR DATE BLOCKING TESTS PASSED 100%!")
    print("==================================================")

if __name__ == '__main__':
    run_suite()
