import unittest
from app import app, GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_USERS

class TestCrossDuplicateRegistrationPrevention(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_cross_duplicate_prevention(self):
        # 1. Register a Customer first
        c_email = "cross_test_customer@shubhlo.com"
        c_phone = "9112233445"
        signup_res = self.app.post('/signup', data={
            'name': 'Rahul Cross Customer',
            'email': c_email,
            'phone': c_phone,
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(signup_res.status_code, 200)
        print("\n[PASS 1] Customer registered successfully!")

        # 2. Attempt to register a Vendor using the SAME Customer Email or Phone
        v_dupe_res = self.app.post('/vendor_register', data={
            'name': 'Duplicate Vendor Lawn',
            'email': c_email, # Duplicate Email
            'phone': '9000000001',
            'service': ['venue'],
            'description': 'Duplicate attempt',
            'govt_id_number': 'MP00011122',
            'password': 'password123',
            'price': '20000',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)
        
        body_text = v_dupe_res.data.decode('utf-8')
        self.assertEqual(v_dupe_res.status_code, 200)
        self.assertIn("alreadyRegModal", body_text)
        self.assertIn("Vendor Already Registered", body_text)
        print("[PASS 2] Vendor registration with existing Customer Email STRICTLY BLOCKED with Already Registered popup!")

        # 3. Register a Vendor first
        v_email = "cross_test_vendor@shubhlo.com"
        v_phone = "9988771122"
        v_reg_res = self.app.post('/vendor_register', data={
            'name': 'Original Vendor Lawn',
            'email': v_email,
            'phone': v_phone,
            'service': ['venue'],
            'description': 'Original vendor lawn',
            'govt_id_number': 'MP00011123',
            'password': 'password123',
            'price': '25000',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)
        self.assertEqual(v_reg_res.status_code, 200)
        print("[PASS 3] Vendor registered successfully!")

        # 4. Attempt to register a Customer using the SAME Vendor Phone
        c_dupe_res = self.app.post('/signup', data={
            'name': 'Attempted Duplicate Customer',
            'email': 'different_email@shubhlo.com',
            'phone': v_phone, # Duplicate Phone
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(c_dupe_res.status_code, 200)
        self.assertIn("already exists", c_dupe_res.data.decode('utf-8').lower())
        print("[PASS 4] Customer registration with existing Vendor Phone STRICTLY BLOCKED with warning message!")

if __name__ == '__main__':
    unittest.main()
