import unittest
import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.path.abspath("."))

from app import urlquote_filter, clean_phone_indian_filter

class TestWhatsAppFilters(unittest.TestCase):

    def test_urlquote_filter(self):
        text = "Namaste Customer! Booking #1025 confirmed 🎉"
        quoted = urlquote_filter(text)
        self.assertIn("%20", quoted)
        self.assertNotIn(" ", quoted)

    def test_clean_phone_indian_filter(self):
        self.assertEqual(clean_phone_indian_filter("9876543210"), "919876543210")
        self.assertEqual(clean_phone_indian_filter("+919876543210"), "919876543210")
        self.assertEqual(clean_phone_indian_filter("919876543210"), "919876543210")

if __name__ == "__main__":
    unittest.main()
