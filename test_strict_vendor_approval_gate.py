import sys
sys.stdout.reconfigure(encoding='utf-8')
import unittest
from app import app, GLOBAL_REGISTERED_VENDORS, fetch_vendors_by_service

class TestStrictVendorApprovalGate(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        GLOBAL_REGISTERED_VENDORS[:] = [v for v in GLOBAL_REGISTERED_VENDORS if v.get('email') != "security_test_vendor@shubhlo.com"]

    def test_vendor_approval_security_gate(self):
        # 1. Register a new vendor
        test_email = "security_test_vendor@shubhlo.com"
        test_phone = "9988776655"
        reg_payload = {
            'name': 'Royal Security Gardens',
            'email': test_email,
            'phone': test_phone,
            'service': 'venue',
            'description': 'Luxury marriage lawn',
            'govt_id_number': 'MP12345678',
            'password': 'password123',
            'price': '35000',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }
        res = self.app.post('/vendor_register', data=reg_payload, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify vendor is Pending in GLOBAL_REGISTERED_VENDORS
        new_v = next((v for v in GLOBAL_REGISTERED_VENDORS if v['email'] == test_email), None)
        self.assertIsNotNone(new_v)
        self.assertEqual(new_v['approval_status'], 'Pending')
        print(f"\n[PASS 1] Vendor registered with status: {new_v['approval_status']}")

        # 2. Check Customer Booking Visibility: Pending vendor MUST NOT be visible
        itarsi_venues = fetch_vendors_by_service('venue', tehsil='Itarsi')
        pending_visible = any(v.get('email') == test_email for v in itarsi_venues)
        self.assertFalse(pending_visible, "SECURITY FAILURE: Pending vendor appeared in customer booking search!")
        print("[PASS 2] Pending vendor correctly EXCLUDED from customer booking search!")

        # 3. Log in as pending vendor and attempt to add a service (/vendor/add_service)
        with self.app.session_transaction() as sess:
            sess['vendor'] = test_email
            sess['vendor_name'] = 'Royal Security Gardens'
            sess['vendor_service'] = 'venue'
            sess['vendor_id'] = new_v['id']

        add_res = self.app.post('/vendor/add_service', data={'service': 'catering', 'price': '450'}, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)
        self.assertIn("PENDING Owner Approval", add_res.data.decode('utf-8'))
        print("[PASS 3] Add service attempt by pending vendor STRICTLY BLOCKED!")

        # 4. Simulate Owner Approval
        new_v['approval_status'] = 'Approved'
        print("[PASS 4] Owner approved the vendor!")

        # 5. Verify that approved vendor CAN now add a service
        add_approved_res = self.app.post('/vendor/add_service', data={'service': 'catering', 'price': '450'}, follow_redirects=True)
        self.assertEqual(add_approved_res.status_code, 200)
        self.assertIn("Successfully added new service category", add_approved_res.data.decode('utf-8'))
        print("[PASS 5] Approved vendor successfully added new service!")

        # 6. Verify approved vendor IS NOW VISIBLE to customers
        updated_itarsi_venues = fetch_vendors_by_service('venue', tehsil='Itarsi')
        approved_visible = any(v.get('email') == test_email for v in updated_itarsi_venues)
        self.assertTrue(approved_visible, "FAILURE: Approved vendor did not appear in customer booking search!")
        print("[PASS 6] Approved vendor correctly APPEARS in customer booking search!")

if __name__ == '__main__':
    unittest.main()
