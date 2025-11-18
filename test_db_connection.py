import os
import sys
import psycopg2
import psycopg2.extras

DATABASE_URL= "postgresql://postgres:gr0up-p4ssw0rd@web-app-database-eks.cv2uwqaiqpjq.ap-southeast-2.rds.amazonaws.com:5432"

def main():
    db_url = DATABASE_URL

    try:
        # short timeout to fail fast in probes
        conn = psycopg2.connect(dsn=db_url, connect_timeout=5)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT 1 AS ok;")
        row = cur.fetchone()
        if row and row.get("ok") == 1:
            print("OK: database connection successful (SELECT 1 returned 1)")
            cur.close()
            conn.close()
            sys.exit(0)
        else:
            print("ERROR: unexpected query result:", row)
            cur.close()
            conn.close()
            sys.exit(1)
    except Exception as e:
        print("ERROR: database connection failed:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
