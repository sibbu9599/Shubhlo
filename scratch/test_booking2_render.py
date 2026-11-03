import sys
sys.path.insert(0, '.')
from app import app

client = app.test_client()

with client.session_transaction() as sess:
    sess['user'] = 'customer@example.com'
    sess['booking_info'] = {
        'name': 'Test Customer',
        'email': 'customer@example.com',
        'phone': '9876543210',
        'event_name': 'Wedding Party',
        'event_date': '2026-11-20',
        'state': 'Madhya Pradesh',
        'district': 'Hoshangabad',
        'tehsil': 'Itarsi',
        'address': 'Near Main Market, Itarsi Road, 461111'
    }

res_b2 = client.get('/booking2')
assert res_b2.status_code == 200, f"/booking2 failed with {res_b2.status_code}"
html_b2 = res_b2.data.decode('utf-8', errors='ignore')

assert 'None' not in html_b2.replace('None of', ''), "Literal 'None' found in /booking2"
print("[PASS] /booking2 rendered with HTTP 200 and zero 'None' bugs.")

res_serv = client.get('/services')
assert res_serv.status_code == 200, f"/services failed with {res_serv.status_code}"
html_serv = res_serv.data.decode('utf-8', errors='ignore')
print("[PASS] /services rendered with HTTP 200.")
print("All page render assertions PASSED successfully!")
