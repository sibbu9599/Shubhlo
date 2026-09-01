import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import app

print("--- Testing Customer & Vendor Login Authentication Security ---")

with app.app.test_client() as client:
    # 1. Unregistered user attempting to login
    res1 = client.post('/login', data={'email': 'unregistered@test.com', 'password': 'wrongpassword'}, follow_redirects=True)
    assert b"Invalid" in res1.data or b"incorrect" in res1.data or b"registered" in res1.data
    print("✓ Test 1 Passed: Unregistered customer login rejected.")

    # 2. Register a new customer
    client.post('/signup', data={'name': 'Rahul Test', 'email': 'rahul@test.com', 'phone': '9876543219', 'password': 'secretpassword'}, follow_redirects=True)

    # 3. Try logging in with WRONG password
    res3 = client.post('/login', data={'email': 'rahul@test.com', 'password': 'wrongpassword'}, follow_redirects=True)
    assert b"Invalid" in res3.data or b"registered" in res3.data
    print("✓ Test 3 Passed: Customer login with WRONG password rejected.")

    # 4. Try logging in with CORRECT password
    res4 = client.post('/login', data={'email': 'rahul@test.com', 'password': 'secretpassword'}, follow_redirects=True)
    assert b"Login successful" in res4.data or b"Welcome" in res4.data
    print("✓ Test 4 Passed: Customer login with CORRECT password accepted.")

    # 5. Unregistered Vendor attempting to login
    res5 = client.post('/vendor/login', data={'email': 'fakevendor@test.com', 'password': 'fakepassword'}, follow_redirects=True)
    assert b"Invalid" in res5.data or b"registered" in res5.data
    print("✓ Test 5 Passed: Unregistered vendor login rejected.")

    # 6. Default Mock Vendor with WRONG password
    res6 = client.post('/vendor/login', data={'email': 'vendor@shubhlo.com', 'password': 'wrongpassword'}, follow_redirects=True)
    assert b"Invalid" in res6.data or b"registered" in res6.data
    print("✓ Test 6 Passed: Vendor login with WRONG password rejected.")

    # 7. Default Mock Vendor with CORRECT password
    res7 = client.post('/vendor/login', data={'email': 'vendor@shubhlo.com', 'password': 'vendor123'}, follow_redirects=True)
    assert b"Vendor Login successful" in res7.data or b"Welcome" in res7.data
    print("✓ Test 7 Passed: Vendor login with CORRECT password accepted.")

print("\n--- ALL AUTHENTICATION SECURITY TESTS PASSED 100%! ---")
