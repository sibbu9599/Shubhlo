import unittest
from app import app, GLOBAL_REGISTERED_VENDORS

class TestVendorServiceSwitching(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_vendor_add_and_switch_services(self):
        # 1. Log in as vendor 'we9599@gmail.com'
        with self.app.session_transaction() as sess:
            sess['vendor'] = 'we9599@gmail.com'
            sess['vendor_name'] = 'we'
            sess['vendor_service'] = 'venue'

        # 2. Access vendor dashboard initially
        resp = self.app.get('/vendor_dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Venue', resp.data)

        # 3. Add 'mehendi' service via /vendor/add_service
        resp_add = self.app.post('/vendor/add_service', data={
            'service': 'mehendi',
            'description': 'Mehendi artist services by WE',
            'price': '3500.00'
        }, follow_redirects=True)
        self.assertEqual(resp_add.status_code, 200)
        self.assertIn(b'MEHENDI', resp_add.data)

        # 4. Switch to 'mehendi' service view
        resp_switch_m = self.app.get('/vendor/switch_service/mehendi', follow_redirects=True)
        self.assertEqual(resp_switch_m.status_code, 200)
        # Check active pill indicator and service name in dashboard
        self.assertIn(b'Mehendi', resp_switch_m.data)
        with self.app.session_transaction() as sess:
            self.assertEqual(sess.get('vendor_service'), 'mehendi')

        # 5. Switch back to 'venue' service view
        resp_switch_v = self.app.get('/vendor/switch_service/venue', follow_redirects=True)
        self.assertEqual(resp_switch_v.status_code, 200)
        with self.app.session_transaction() as sess:
            self.assertEqual(sess.get('vendor_service'), 'venue')

if __name__ == '__main__':
    unittest.main()
