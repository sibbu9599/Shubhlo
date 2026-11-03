import pymysql
import json
import sys
from datetime import datetime, date

# Force UTF-8 stdout if needed
sys.stdout.reconfigure(encoding='utf-8')

def default_converter(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)

def inspect_db():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Sibbu9599@',
        database='shubhlo_db',
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES;")
        tables = [list(r.values())[0] for r in cur.fetchall()]
        print(f"DATABASE: shubhlo_db (Total Tables: {len(tables)})\n")
        
        for tbl in tables:
            cur.execute(f"DESCRIBE `{tbl}`;")
            columns = cur.fetchall()
            cur.execute(f"SELECT COUNT(*) as cnt FROM `{tbl}`;")
            count = cur.fetchone()['cnt']
            
            print("==================================================")
            print(f"TABLE: {tbl} (Rows: {count})")
            print("--------------------------------------------------")
            print("Columns:")
            for col in columns:
                extra = f" [{col['Extra']}]" if col['Extra'] else ""
                key = f" [{col['Key']}]" if col['Key'] else ""
                null_str = "NULL" if col['Null'] == 'YES' else "NOT NULL"
                print(f"  - {col['Field']} : {col['Type']} {null_str}{key}{extra}")
            
            if count > 0:
                cur.execute(f"SELECT * FROM `{tbl}` LIMIT 10;")
                rows = cur.fetchall()
                print(f"\nData ({min(count, 10)} of {count} rows):")
                print(json.dumps(rows, indent=2, default=default_converter, ensure_ascii=False))
            else:
                print("\nStatus: [Khali hai / 0 records]")
            print("\n")

    conn.close()

if __name__ == '__main__':
    inspect_db()
