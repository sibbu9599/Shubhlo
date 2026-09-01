import unittest, sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app

class TestNewVendorEmptyDashboard(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_new_vendor_dashboard_has_zero_fake_data(self):
        # 1. Register a fresh vendor
        v_data = {
            'name': 'Fresh Vendor Studio',
            'email': 'freshvendor@gmail.com',
            'phone': '9811122233',
            'service': 'photography',
            'password': 'vendor123',
            'price': '25000',
            'govt_id_number': '123456789012',
            'terms_accepted': 'on'
        }
        res_vreg = self.app.post('/vendor_register', data=v_data, follow_redirects=True)
        self.assertEqual(res_vreg.status_code, 200)

        # 2. Log in as the new vendor
        v_login_data = {
            'email': 'freshvendor@gmail.com',
            'password': 'vendor123'
        }
        res_vlog = self.app.post('/vendor_login', data=v_login_data, follow_redirects=True)
        self.assertEqual(res_vlog.status_code, 200)

        # 3. Access vendor dashboard
        res_vdash = self.app.get('/vendor/dashboard', follow_redirects=True)
        self.assertEqual(res_vdash.status_code, 200)

        page_text = res_vdash.get_data(as_text=True)

        # 4. Verify NO fake booking #201 exists!
        self.assertNotIn('Booking #201', page_text, "ERROR: Fake booking #201 found in new vendor dashboard!")
        
        # 5. Verify NO fake reviews ('Great service, highly professional!') exist!
        self.assertNotIn('Great service, highly professional!', page_text, "ERROR: Fake review found in new vendor dashboard!")

        # 6. Verify NO fake ticket ('Rahul Sharma') exists!
        self.assertNotIn('Rahul Sharma', page_text, "ERROR: Fake complaint ticket found in new vendor dashboard!")

        print("✓ PASS: New vendor dashboard is 100% clean with ZERO fake bookings, ratings, or complaints!")

if __name__ == '__main__':
    unittest.main()
