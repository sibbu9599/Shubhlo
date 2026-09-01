import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from app import app

client = app.test_client()

with client:
    with client.session_transaction() as sess:
        sess['user'] = 'customer@example.com'
        sess['user_name'] = 'Customer User'
        sess['mock_bookings'] = [{
            'id': 201,
            'name': 'Customer User',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Main St',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'event_date': '2026-12-25',
            'amount': 50000.0,
            'token_deposit': 5000.0,
            'payment_status': 'Paid',
            'payment_method': 'UPI',
            'status': 'Pending Admin Approval',
            'booking_status': 'Pending Admin Approval',
            'venue': 'Royal Palace'
        }]

    res1 = client.get('/dashboard')
    html1 = res1.get_data(as_text=True)

    lines = html1.splitlines()
    for idx, line in enumerate(lines, 1):
        if "status-confirmed" in line or "Confirmed" in line:
            print(f"Line {idx}: {line.strip()}")
