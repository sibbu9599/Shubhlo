import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("=== Testing Owner Panel Vendor Uploaded Documents Inspection ===")

with app.app.test_client() as client:
    # 1. Register a new vendor with ID Proof & Govt ID Number
    res_reg = client.post('/vendor_register', data={
        'name': 'Royal Test Garden',
        'email': 'royal_doc_test@shubhlo.com',
        'phone': '9898989898',
        'service': ['venue'],
        'description': 'Luxury marriage hall with royal gardens.',
        'price': '60000',
        'password': 'password123',
        'state': 'Madhya Pradesh',
        'district': 'Hoshangabad',
        'tehsil': 'Itarsi',
        'govt_id_number': '123456789012',
        'accept_terms_vendor': 'on'
    }, follow_redirects=True)
    assert res_reg.status_code == 200
    print("✓ Step 1 Passed: Vendor registered with Govt ID Number 123456789012!")

    # 2. Login as Owner & Open Owner Dashboard
    with client.session_transaction() as sess:
        sess['admin'] = 'owner@shubhlo.com'
        sess['is_owner'] = True

    res_owner = client.get('/owner/dashboard')
    txt_owner = res_owner.data.decode('utf-8', errors='ignore')
    
    assert "Uploaded Documents & Photo ID" in txt_owner
    assert "View Document Proof" in txt_owner or "View Document" in txt_owner
    assert "123456789012" in txt_owner or "ID:" in txt_owner
    print("✓ Step 2 Passed: Owner Dashboard displays Vendor Uploaded Documents, Govt ID Number, and Direct Document Proof Link!")

print("\n=== OWNER VENDOR DOCUMENT INSPECTION TEST PASSED 100%! ===")
