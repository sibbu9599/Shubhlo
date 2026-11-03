import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, GLOBAL_PERMITTED_LOCATIONS, DEFAULT_PERMITTED_LOCATIONS

def run_tests():
    print("==================================================")
    print("STARTING MASTER LOCATION CONTROL SUITE TEST")
    print("==================================================")

    client = app.test_client()

    # 1. Test /api/allowed-locations initial state
    print("\n[Test 1] Testing /api/allowed-locations initial response...")
    resp = client.get('/api/allowed-locations')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = json.loads(resp.data.decode('utf-8'))
    print(f"  Received states: {list(data.keys())}")
    assert 'Madhya Pradesh' in data, "Madhya Pradesh should be in allowed locations"
    assert 'Hoshangabad' in data['Madhya Pradesh'], "Hoshangabad should be in MP"
    assert 'Itarsi' in data['Madhya Pradesh']['Hoshangabad'], "Itarsi should be in Hoshangabad"
    print("  PASS: /api/allowed-locations returns active locations tree.")

    # 2. Test Owner Dashboard rendering
    print("\n[Test 2] Testing Owner Dashboard access and rendering...")
    with client.session_transaction() as sess:
        sess['admin'] = 'owner@shubhlo.com'
        sess['is_owner'] = True

    resp = client.get('/owner_dashboard')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.data.decode('utf-8')
    assert 'State, District & Tehsil Master Command Center' in html
    assert 'Active States' in html
    assert 'Total Tehsils' in html
    assert 'Itarsi' in html
    print("  PASS: Owner Dashboard renders Master Location Command Center with metrics.")

    # 3. Test Owner Adding New Locations (multiple comma-separated tehsils)
    print("\n[Test 3] Testing adding new location (Madhya Pradesh > Harda > Harda, Timarni, Khirkiya)...")
    add_resp = client.post('/owner_add_location', data={
        'state': 'Madhya Pradesh',
        'district': 'Harda',
        'tehsil': 'Harda, Timarni, Khirkiya'
    }, follow_redirects=True)
    assert add_resp.status_code == 200

    resp2 = client.get('/api/allowed-locations')
    data2 = json.loads(resp2.data.decode('utf-8'))
    assert 'Harda' in data2['Madhya Pradesh'], "Harda district should now exist"
    assert 'Timarni' in data2['Madhya Pradesh']['Harda'], "Timarni should be in Harda"
    assert 'Khirkiya' in data2['Madhya Pradesh']['Harda'], "Khirkiya should be in Harda"
    print("  PASS: Added Harda with multiple tehsils successfully!")

    # 4. Test Toggling Location Status (Pausing Timarni)
    print("\n[Test 4] Testing pausing Timarni...")
    # Find Timarni ID
    with client.session_transaction() as sess:
        locs = sess.get('permitted_locations', GLOBAL_PERMITTED_LOCATIONS)
        timarni_loc = next((l for l in locs if l['tehsil'].lower() == 'timarni'), None)
        assert timarni_loc is not None, "Timarni location not found in session"
        timarni_id = timarni_loc['id']

    toggle_resp = client.post(f'/owner_toggle_location/{timarni_id}', follow_redirects=True)
    assert toggle_resp.status_code == 200

    resp3 = client.get('/api/allowed-locations')
    data3 = json.loads(resp3.data.decode('utf-8'))
    harda_tehsils = data3['Madhya Pradesh'].get('Harda', [])
    assert 'Timarni' not in harda_tehsils, f"Paused tehsil 'Timarni' should NOT appear in active API, but found: {harda_tehsils}"
    assert 'Harda' in harda_tehsils, "Active tehsil 'Harda' should still appear"
    print("  PASS: Paused Timarni is immediately hidden from customer booking & vendor dropdowns!")

    # 5. Test Resuming Timarni
    print("\n[Test 5] Testing resuming Timarni (Go Live)...")
    toggle_resume = client.post(f'/owner_toggle_location/{timarni_id}', follow_redirects=True)
    assert toggle_resume.status_code == 200

    resp4 = client.get('/api/allowed-locations')
    data4 = json.loads(resp4.data.decode('utf-8'))
    assert 'Timarni' in data4['Madhya Pradesh'].get('Harda', []), "Timarni should now be active again"
    print("  PASS: Timarni resumed and live again in API!")

    # 6. Test Editing Location (Rename Khirkiya to Khirkiya Mandi)
    print("\n[Test 6] Testing editing location...")
    with client.session_transaction() as sess:
        locs = sess.get('permitted_locations', GLOBAL_PERMITTED_LOCATIONS)
        khirkiya_loc = next((l for l in locs if l['tehsil'].lower() == 'khirkiya'), None)
        assert khirkiya_loc is not None, "Khirkiya location not found"
        khirkiya_id = khirkiya_loc['id']

    edit_resp = client.post(f'/owner_edit_location/{khirkiya_id}', data={
        'state': 'Madhya Pradesh',
        'district': 'Harda',
        'tehsil': 'Khirkiya Mandi'
    }, follow_redirects=True)
    assert edit_resp.status_code == 200

    resp5 = client.get('/api/allowed-locations')
    data5 = json.loads(resp5.data.decode('utf-8'))
    assert 'Khirkiya Mandi' in data5['Madhya Pradesh'].get('Harda', []), "Khirkiya Mandi should appear in API"
    assert 'Khirkiya' not in data5['Madhya Pradesh'].get('Harda', []), "Old Khirkiya should be gone"
    print("  PASS: Edited location name updated in real-time!")

    # 7. Test Deleting Location (Delete Timarni)
    print("\n[Test 7] Testing deleting location...")
    del_resp = client.post(f'/owner_delete_location/{timarni_id}', follow_redirects=True)
    assert del_resp.status_code == 200

    resp6 = client.get('/api/allowed-locations')
    data6 = json.loads(resp6.data.decode('utf-8'))
    assert 'Timarni' not in data6['Madhya Pradesh'].get('Harda', []), "Timarni should be deleted"
    print("  PASS: Location deleted permanently!")

    # 8. Test Booking1 page rendering
    print("\n[Test 8] Testing /booking1 template rendering with user session...")
    with client.session_transaction() as sess:
        sess['user'] = 'testuser@gmail.com'
        sess['user_name'] = 'Test Host'

    b_resp = client.get('/booking1')
    assert b_resp.status_code == 200
    b_html = b_resp.data.decode('utf-8')
    assert 'Event Booking Details' in b_html
    assert 'api/allowed-locations' in b_html
    print("  PASS: /booking1 renders smoothly!")

    # 9. Test Vendor Register page rendering
    print("\n[Test 9] Testing /vendor_register template rendering...")
    v_resp = client.get('/vendor_register')
    assert v_resp.status_code == 200
    v_html = v_resp.data.decode('utf-8')
    assert 'api/allowed-locations' in v_html
    print("  PASS: /vendor_register renders smoothly!")

    print("\n==================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()

