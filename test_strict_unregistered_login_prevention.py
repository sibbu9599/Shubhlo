import unittest
from app import app, GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_USERS

class TestStrictUnregisteredLoginPrevention(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_unregistered_customer_login_blocked(self):
        # 1. Attempt Customer Login with completely random unregistered credentials
        unregistered_email = "non_existent_cust_99999@shubhlo.com"
        res = self.app.post('/login', data={
            'email': unregistered_email,
            'password': 'random_password_123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        body = res.data.decode('utf-8')
        # Ensure login failed and user was NOT logged in
        self.assertIn("Only registered users can log in", body)
        self.assertNotIn("Welcome back", body)
        print("\n[PASS 1] Unregistered Customer Login strictly blocked with Unregistered alert!")

    def test_unregistered_vendor_login_blocked(self):
        # 2. Attempt Vendor Login with completely random unregistered credentials
        unregistered_email = "non_existent_vend_88888@shubhlo.com"
        res = self.app.post('/vendor_login', data={
            'email': unregistered_email,
            'password': 'random_password_123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        body = res.data.decode('utf-8')
        # Ensure vendor login failed and vendor dashboard was NOT accessed
        self.assertIn("Only registered vendors can log in", body)
        self.assertNotIn("Vendor Login successful", body)
        print("[PASS 2] Unregistered Vendor Login strictly blocked with Unregistered alert!")

    def test_registered_customer_login_succeeds(self):
        # 3. Register a Customer first, then test login
        c_email = "valid_reg_cust_777@shubhlo.com"
        c_pass = "securepass123"
        self.app.post('/signup', data={
            'name': 'Valid Reg Customer',
            'email': c_email,
            'phone': '9988776655',
            'password': c_pass
        }, follow_redirects=True)

        res = self.app.post('/login', data={
            'email': c_email,
            'password': c_pass
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        body = res.data.decode('utf-8')
        self.assertIn("Login successful", body)
        print("[PASS 3] Registered Customer Login successfully allowed!")

    def test_registered_vendor_login_succeeds(self):
        # 4. Register a Vendor first, then test login
        v_email = "valid_reg_vend_666@shubhlo.com"
        v_pass = "securepass123"
        self.app.post('/vendor_register', data={
            'name': 'Valid Reg Vendor Lawn',
            'email': v_email,
            'phone': '8877665544',
            'service': ['venue'],
            'description': 'Valid vendor description',
            'govt_id_number': 'MP00011199',
            'password': v_pass,
            'price': '30000',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)

        res = self.app.post('/vendor_login', data={
            'email': v_email,
            'password': v_pass
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        body = res.data.decode('utf-8')
        self.assertIn("Vendor Login successful", body)
        print("[PASS 4] Registered Vendor Login successfully allowed!")

if __name__ == '__main__':
    unittest.main()
