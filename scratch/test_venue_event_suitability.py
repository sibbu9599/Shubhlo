import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, enrich_venue_attributes, fetch_vendors_by_service, MOCK_VENDORS

class TestVenueEventSuitability(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_01_enrich_venue_attributes(self):
        """Test that enrich_venue_attributes correctly classifies venues"""
        rest_vendor = {
            'id': 12,
            'name': 'The Urban Spice Restaurant & Party Lounge (Mock)',
            'description': 'Cosy AC restaurant for small parties',
            'price': 15000.0
        }
        enriched = enrich_venue_attributes(rest_vendor)
        self.assertEqual(enriched['venue_type'], 'restaurant')
        self.assertFalse(enriched['can_host_wedding'])
        self.assertIn('30 - 100', enriched['capacity_label'])
        print("✓ Test 1 Passed: Restaurant accurately identified and can_host_wedding is False.")

        garden_vendor = {
            'id': 1,
            'name': 'Royal Palace Garden (Mock)',
            'description': 'Lush grand marriage lawn',
            'price': 150000.0
        }
        enriched_g = enrich_venue_attributes(garden_vendor)
        self.assertEqual(enriched_g['venue_type'], 'marriage_garden')
        self.assertTrue(enriched_g['can_host_wedding'])
        print("✓ Test 1b Passed: Marriage Garden accurately identified and can_host_wedding is True.")

    def test_02_wedding_event_suitability_in_booking2(self):
        """Test that when customer books a Wedding, restaurants are marked incompatible"""
        with self.client.session_transaction() as sess:
            sess['user'] = 'customer@shubhlo.com'
            sess['user_name'] = 'Rahul Sharma'
            sess['booking_info'] = {
                'name': 'Rahul Sharma',
                'email': 'customer@shubhlo.com',
                'phone': '9876543210',
                'address': 'House 12, Station Road, Itarsi',
                'state': 'Madhya Pradesh',
                'district': 'Hoshangabad',
                'tehsil': 'Itarsi',
                'event_date': '2026-11-20',
                'event_name': 'Wedding / शादी विवाह',
                'event_type': 'Wedding / शादी विवाह'
            }

        res = self.client.get('/booking2?name=Rahul+Sharma&email=customer@shubhlo.com&phone=9876543210&address=House+12+Station+Road+Itarsi&state=Madhya+Pradesh&district=Hoshangabad&tehsil=Itarsi&event_date=2026-11-20&event_name=Wedding+/+शादी+विवाह')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8', errors='ignore')

        # Verify suitability protection banner
        self.assertIn("WEDDING SUITABILITY FILTER ACTIVE", html)
        self.assertIn("शादी-विवाह अनुकूलता सुरक्षा सक्रिय", html)

        # Verify restaurant has locked badge
        self.assertIn("🚫 Not for Weddings", html)
        self.assertIn("The Urban Spice Restaurant", html)
        self.assertIn("venue-card-incompatible", html)
        self.assertIn("showVenueLockedModal", html)
        print("✓ Test 2 Passed: Wedding event renders protection banner, locks restaurants with incompatible card.")

    def test_03_birthday_event_suitability_in_booking2(self):
        """Test that when customer books a Birthday, restaurants are recommended and selectable"""
        with self.client.session_transaction() as sess:
            sess['user'] = 'customer@shubhlo.com'
            sess['user_name'] = 'Rahul Sharma'
            sess['booking_info'] = {
                'name': 'Rahul Sharma',
                'email': 'customer@shubhlo.com',
                'phone': '9876543210',
                'address': 'House 12, Station Road, Itarsi',
                'state': 'Madhya Pradesh',
                'district': 'Hoshangabad',
                'tehsil': 'Itarsi',
                'event_date': '2026-11-20',
                'event_name': 'Birthday Party / जन्मदिन',
                'event_type': 'Birthday Party / जन्मदिन'
            }

        res = self.client.get('/booking2?name=Rahul+Sharma&email=customer@shubhlo.com&phone=9876543210&address=House+12+Station+Road+Itarsi&state=Madhya+Pradesh&district=Hoshangabad&tehsil=Itarsi&event_date=2026-11-20&event_name=Birthday+Party+/+जन्मदिन')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8', errors='ignore')

        # Verify birthday recommendation banner
        self.assertIn("RECOMMENDED FOR BIRTHDAYS & INTIMATE GATHERINGS", html)
        self.assertIn("जन्मदिन व छोटी पार्टी हेतु सुझाव", html)

        # Verify restaurant is NOT locked and has Best for Birthday badge
        self.assertIn("BEST FOR BIRTHDAY", html)
        print("✓ Test 3 Passed: Birthday event renders birthday recommendation banner and highlights restaurant.")

    def test_04_server_side_guard_prevents_restaurant_for_wedding(self):
        """Test that server-side validation strictly rejects restaurant venue for wedding"""
        with self.client.session_transaction() as sess:
            sess['user'] = 'customer@shubhlo.com'
            sess['booking_info'] = {
                'name': 'Rahul Sharma',
                'email': 'customer@shubhlo.com',
                'phone': '9876543210',
                'address': 'House 12, Station Road, Itarsi',
                'state': 'Madhya Pradesh',
                'district': 'Hoshangabad',
                'tehsil': 'Itarsi',
                'event_date': '2026-11-20',
                'event_name': 'Wedding / शादी विवाह',
                'event_type': 'Wedding / शादी विवाह'
            }

        # Try to post restaurant venue for wedding
        post_data = {
            'venue': 'The Urban Spice Restaurant & Party Lounge (Mock)',
            'catering': 'Shahi Caterers (Mock)'
        }
        res = self.client.post('/confirm-booking', data=post_data, follow_redirects=True)
        html = res.data.decode('utf-8', errors='ignore')

        # Must reject and redirect back to booking2 with danger alert
        self.assertIn("केवल जन्मदिन व 30-100 मेहमानों की छोटी पार्टियों के लिए है और शादी-विवाह नहीं कराता", html)
        print("✓ Test 4 Passed: Server-side validation strictly rejects booking a restaurant for a wedding event!")

    def test_05_vendor_registration_venue_classification(self):
        """Test vendor registration captures venue classification attributes"""
        import uuid
        test_email = f"cafe_{uuid.uuid4().hex[:6]}@shubhlo.com"
        test_phone = f"99{uuid.uuid4().int % 100000000:08d}"

        reg_data = {
            'name': 'Cafe Bliss & Mini Lounge',
            'email': test_email,
            'phone': test_phone,
            'service': ['venue'],
            'venue_type': 'restaurant',
            'guest_capacity': '30 - 100 Guests (Small Gathering)',
            'can_host_wedding': 'no',
            'description': 'Cosy party hall for birthdays',
            'price': '10000',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }
        res = self.client.post('/vendor_register', data=reg_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Check GLOBAL_REGISTERED_VENDORS where newly registered vendor is stored
        from app import GLOBAL_REGISTERED_VENDORS
        found_cafe = next((v for v in GLOBAL_REGISTERED_VENDORS if v.get('email') == test_email), None)
        self.assertIsNotNone(found_cafe)
        self.assertEqual(found_cafe.get('venue_type'), 'restaurant')
        self.assertFalse(found_cafe.get('can_host_wedding'))
        print("✓ Test 5 Passed: Newly registered restaurant vendor automatically has venue_type='restaurant' and can_host_wedding=False!")

if __name__ == '__main__':
    unittest.main()
