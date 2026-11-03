import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import get_db_connection

conn = get_db_connection()
with conn.cursor() as c:
    c.execute('DESCRIBE users')
    print('USERS:')
    for row in c.fetchall():
        print(row)
    c.execute('DESCRIBE vendor')
    print('\nVENDOR:')
    for row in c.fetchall():
        print(row)
    c.execute("SHOW TABLES LIKE 'simulated_sms'")
    print('\nSIMULATED SMS TABLE:', c.fetchall())
conn.close()
