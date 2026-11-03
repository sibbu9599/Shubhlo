import pymysql

passwords = ['', 'root', 'admin', 'password', '123456', 'shubhlo']
hosts = ['localhost', '127.0.0.1']

for h in hosts:
    for p in passwords:
        try:
            conn = pymysql.connect(host=h, user='root', password=p, port=3306, connect_timeout=1)
            print(f"CONNECTED: host={h}, pwd='{p}'")
            with conn.cursor() as cur:
                cur.execute("SHOW DATABASES;")
                print("Databases:", cur.fetchall())
            conn.close()
        except Exception as e:
            print(f"Error host={h}, pwd='{p}': {e}")
