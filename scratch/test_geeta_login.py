import sys
import unittest
from app import app, load_fallback_data

class TestGeetaLogin(unittest.TestCase):
    def setUp(self):
        load_fallback_data()
        self.client = app.test_client()

    def test_geeta_customer_login(self):
        res = self.client.post('/login', data={
            'email': 'geeta9599@gmail.com',
            'password': 'Password123'
        }, follow_redirects=True)
        html = res.data.decode('utf-8')
        self.assertIn('Welcome back', html)
        print("SUCCESS: geeta9599@gmail.com customer login verified successfully!")

if __name__ == '__main__':
    unittest.main()
