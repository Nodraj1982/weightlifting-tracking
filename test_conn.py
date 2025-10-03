import psycopg2

uri = "postgres://postgres.snltqtknffxtqhqcqbgg:EpPrBKOkXV0prQL7@aws-1-eu-west-2.pooler.supabase.com:6543/postgres"

try:
    conn = psycopg2.connect(uri)
    cur = conn.cursor()
    cur.execute("select current_database(), current_user;")
    print("Connected as:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print("Failed:", e)