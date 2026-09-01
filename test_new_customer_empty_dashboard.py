import unittest, sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app

class TestNewCustomerEmptyDashboard(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_new_customer_dashboard_has_zero_fake_data(self):
        # 1. Register a fresh customer
        signup_data = {
            'name': 'Clean Customer',
            'email': 'cleancustomer@gmail.com',
            'phone': '9888877777',
            'password': 'password123'
        }
        res_signup = self.app.post('/signup', data=signup_data, follow_redirects=True)
        self.assertEqual(res_signup.status_code, 200)

        # 2. Log in as the new customer
        login_data = {
            'email': 'cleancustomer@gmail.com',
            'password': 'password123'
        }
        res_login = self.app.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)

        # 3. Access customer dashboard
        res_dash = self.app.get('/dashboard')
        self.assertEqual(res_dash.status_code, 200)

        page_text = res_dash.get_data(as_text=True)

        # 4. Verify NO fake mock booking exists!
        self.assertNotIn('Royal Palace Garden (Mock)', page_text, "ERROR: Fake mock booking found in fresh customer dashboard!")
        
        # 5. Verify NO fake contact inquiry ('Looking for a marriage garden with catering for 500 guests') exists!
        self.assertNotIn('Looking for a marriage garden with catering for 500 guests', page_text, "ERROR: Fake contact inquiry found in fresh customer dashboard!")

        # 6. Verify NO fake support ticket ('Booking Date Change Process') exists!
        self.assertNotIn('Booking Date Change Process', page_text, "ERROR: Fake support ticket found in fresh customer dashboard!")

        print("✓ PASS: Fresh customer dashboard is 100% clean with ZERO fake bookings, contact inquiries, or support tickets!")

if __name__ == '__main__':
    unittest.main()
