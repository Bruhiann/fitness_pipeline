"""
extract_load.py
Reads CSVs from ../data/ and loads them into raw schema in Postgres.
Run after `docker compose up -d` and the healthcheck passes.
"""

import os
import csv
import time
import psycopg2
from psycopg2.extras import execute_values

# Connection config 
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "fitness_db"),
    "user":     os.getenv("DB_USER",     "fitness_user"),
    "password": os.getenv("DB_PASS",     "fitness_pass"),
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# Helpers 
def connect(retries: int = 10, delay: int = 3) -> psycopg2.extensions.connection:
    """Wait for Postgres to be ready, then return a connection."""
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print(" Connected to Postgres.")
            return conn
        except psycopg2.OperationalError as e:
            print(f"   Attempt {attempt}/{retries} – DB not ready yet: {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to Postgres after multiple retries.")


def load_csv(conn, filepath: str, table: str, columns: list[str], truncate: bool = True):
    """Truncate the target table and bulk-insert rows from a CSV."""
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        rows = [
            tuple(row.get(col) or None for col in columns)
            for row in reader
        ]

    with conn.cursor() as cur:
        if truncate:
            cur.execute(f"TRUNCATE TABLE {table};")
            print(f"   Truncated {table}.")

        execute_values(
            cur,
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s",
            rows,
        )
        print(f"   Inserted {len(rows)} rows into {table}.")

    conn.commit()


# Main
def main():
    conn = connect()

    print("\n── Loading workout_log ──────────────────────────────")
    load_csv(
        conn,
        filepath=os.path.join(DATA_DIR, "workout_log.csv"),
        table="raw.workout_log",
        columns=["date", "day_type", "exercise", "side", "set_number", "weight_lbs", "reps"],
    )

    print("\n── Loading weight_log ───────────────────────────────")
    load_csv(
        conn,
        filepath=os.path.join(DATA_DIR, "weight_log.csv"),
        table="raw.weight_log",
        columns=["date", "weight_lbs"],
    )

    conn.close()
    print("\n EL complete. Run `dbt run` to execute transformations.")


if __name__ == "__main__":
    main()
