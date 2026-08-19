import psycopg2
import sys

try:
    conn = psycopg2.connect(host='localhost', port=5433, dbname='echo', user='echo_user', password='echo_pass_2026')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("ALTER TABLE simulations ADD COLUMN IF NOT EXISTS dataset_name VARCHAR(50) DEFAULT 'gasoline'")
    print("Successfully added dataset_name column to the simulations table.")
    conn.close()
except Exception as e:
    print(f"Database not running or accessible yet. Ensure 'docker-compose up -d' has been run. Error: {e}")
