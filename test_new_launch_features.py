import unittest, sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app

class TestNewLaunchFeatures(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_budget_calculator_route_redirect(self):
        """Test Event Budget Calculator route redirects cleanly to /services"""
        res = self.app.get('/budget-calculator')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/services', res.headers['Location'])
        print("\n✓ [PASS 1] Budget Calculator route successfully redirects to services!")

    def test_02_guest_manager_route_redirect(self):
        """Test Guest RSVP Manager route redirects cleanly to /services"""
        res = self.app.get('/guest-manager')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/services', res.headers['Location'])
        print("✓ [PASS 2] Guest RSVP Manager route successfully redirects to services!")

    def test_03_vendor_earnings_analytics_rendering(self):
        """Test Vendor Dashboard Earnings & Monthly Performance Card"""
        with self.app.session_transaction() as sess:
            sess['vendor'] = 'vendor@test.com'
            sess['vendor_name'] = 'Test Vendor'
            sess['vendor_service'] = 'venue'

        res = self.app.get('/vendor/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Earnings & Monthly Performance Analytics', res.data)
        print("✓ [PASS 4] Vendor Earnings & Monthly Revenue Trend card verified!")

if __name__ == '__main__':
    unittest.main()
