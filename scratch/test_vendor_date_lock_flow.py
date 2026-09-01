import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Complete Vendor Date Block & Unblock Cycle ===")

with app.app.test_client() as client:
    # 1. Login as Mock Vendor
    client.post('/vendor/login', data={'email': 'vendor@shubhlo.com', 'password': 'vendor123'}, follow_redirects=True)

    # 2. Block Date 2026-12-31
    test_date = '2026-12-31'
    res_block = client.post('/vendor/toggle_date_availability', data={'event_date': test_date, 'action': 'block', 'reason': 'Marriage Event'}, follow_redirects=True)
    assert b"BUSY" in res_block.data or b"blocked" in res_block.data or b"BLOCKED" in res_block.data
    print("✓ Step 1 Passed: Vendor successfully blocked date 2026-12-31.")

    # 3. Verify Customer sees Vendor as BLOCKED for 2026-12-31
    with client.session_transaction() as sess:
        sess['user'] = 'customer@test.com'

    vendors_on_blocked_date = app.fetch_vendors_by_service('venue', 'Itarsi', test_date)
    target_v = next((v for v in vendors_on_blocked_date if 'Royal Palace' in v['name']), None)
    assert target_v is not None
    assert target_v['is_blocked'] == True
    print("✓ Step 2 Passed: Customer receives is_blocked=True for date 2026-12-31.")

    # 4. Vendor UNBLOCKS Date 2026-12-31
    res_unblock = client.post('/vendor/toggle_date_availability', data={'event_date': test_date, 'action': 'unblock'}, follow_redirects=True)
    assert b"OPEN" in res_unblock.data or b"unblocked" in res_unblock.data or b"upalabdha" in res_unblock.data
    print("✓ Step 3 Passed: Vendor successfully UNBLOCKED date 2026-12-31.")

    # 5. Verify Customer sees Vendor as OPEN for 2026-12-31 after unblocking
    vendors_on_unblocked_date = app.fetch_vendors_by_service('venue', 'Itarsi', test_date)
    target_v_after = next((v for v in vendors_on_unblocked_date if 'Royal Palace' in v['name']), None)
    assert target_v_after is not None
    assert target_v_after['is_blocked'] == False
    print("✓ Step 4 Passed: Customer receives is_blocked=False and can book vendor for date 2026-12-31!")

print("\n=== VENDOR DATE BLOCK & UNBLOCK FLOW TEST PASSED 100%! ===")
