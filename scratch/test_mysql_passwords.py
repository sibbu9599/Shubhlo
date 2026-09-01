import pymysql

passwords_to_try = ['', 'root', 'admin', 'password', '123456', '1234']
ports_to_try = [3306, 3307]

connected = False
for port in ports_to_try:
    for pwd in passwords_to_try:
        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password=pwd,
                port=port,
                connect_timeout=3
            )
            print(f"✅ SUCCESS! Connected to MySQL on port {port} with password '{pwd}'")
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES;")
                dbs = cursor.fetchall()
                print("Databases:", dbs)
            conn.close()
            connected = True
            break
        except Exception as e:
            print(f"Tried port {port}, pwd '{pwd}': {e}")
    if connected:
        break
