import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_db_connection

def main():
    conn = get_db_connection()
    if conn is None:
        print("RESULT: MySQL Connection is OFF / Failed (Using Simulation / Session fallback mode).")
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, phone, service, approval_status FROM vendor ORDER BY id DESC")
            vendors = cursor.fetchall()
            print(f"RESULT: Found {len(vendors)} vendors in MySQL DB:")
            for v in vendors:
                print(f" - ID: {v['id']} | Name: {v['name']} | Email: {v['email']} | Service: {v['service']} | Status: {v['approval_status']}")
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
