import pymysql
import sys
import os

def clean_and_truncate_db():
    print("Connecting to MySQL shubhlo_db to truncate user, vendor, booking & rating tables...")
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='shubhlo_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            tables_to_truncate = [
                "booking_verification",
                "selected_services",
                "simulated_sms",
                "vendor_availability",
                "booking",
                "rating",
                "contact_messages",
                "vendor",
                "users"
            ]

            for table in tables_to_truncate:
                try:
                    cursor.execute(f"TRUNCATE TABLE {table}")
                    print(f"✓ Table '{table}' TRUNCATED successfully.")
                except Exception as ex:
                    print(f"Notice on table '{table}': {ex}")

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()
        conn.close()
        print("🎉 Database clean-up completed 100%!")
    except Exception as e:
        print(f"Database connection / truncate notice: {e}")

if __name__ == "__main__":
    clean_and_truncate_db()
