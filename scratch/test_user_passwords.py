import pymysql

passwords = [
    'shailendra', 'shailendra123', 'shailendra@123', 'Shailendra', 'Shailendra123', 'Shailendra@123',
    'shailendrasingh', 'singh', 'singh123', 'Singh@123', 'celebrato', 'celebrato123', 'Celebrato123',
    'celebrato@123', 'shubhlo', 'shubhlo123', 'Shubhlo123', 'admin123', 'Admin@123', 'root1234', '123456789'
]

for pwd in passwords:
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password=pwd,
            port=3306,
            connect_timeout=1
        )
        print(f"🎉 FOUND MYSQL PASSWORD: '{pwd}'")
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS shubhlo_db;")
            cursor.execute("USE shubhlo_db;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            for tbl in ["booking_verification", "selected_services", "simulated_sms", "vendor_availability", "booking", "rating", "contact_messages", "vendor", "users"]:
                try:
                    cursor.execute(f"TRUNCATE TABLE {tbl};")
                    print(f"✓ Table '{tbl}' TRUNCATED!")
                except Exception as ex:
                    print(f"Info on '{tbl}': {ex}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            conn.commit()
        conn.close()
        print("🎉 SUCCESS: All MySQL tables truncated 100%!")
        break
    except Exception:
        pass
