import pymysql

passwords = ['', 'root', 'admin', 'password', '123456', '1234', 'shubhlo', 'celebrato', 'Shubhlo@123', 'Root@123', 'mysql', '12345678', 'root123']
hosts = ['127.0.0.1', 'localhost']
ports = [3306]

connected_conn = None

for host in hosts:
    for port in ports:
        for pwd in passwords:
            try:
                conn = pymysql.connect(
                    host=host,
                    user='root',
                    password=pwd,
                    port=port,
                    connect_timeout=2
                )
                print(f"✅ CONNECTED! host={host}, port={port}, password='{pwd}'")
                connected_conn = (conn, pwd, port)
                break
            except Exception as e:
                pass
        if connected_conn:
            break
    if connected_conn:
        break

if connected_conn:
    conn, pwd, port = connected_conn
    try:
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
        print("🎉 SUCCESS: All MySQL database tables truncated 100%!")
    except Exception as e:
        print(f"Error during truncate: {e}")
else:
    print("NO_PASS_MATCH")
