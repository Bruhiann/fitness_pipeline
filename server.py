"""
server.py
A lightweight Flask API that serves data from Postgres dbt mart tables.
Run with: python server.py
Then open dashboard/index.html in your browser.
"""

import os
import json
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras

app = Flask(__name__, static_folder='dashboard', static_url_path='')
CORS(app)

@app.route('/')
def dashboard():
    return app.send_static_file('index.html')

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "fitness_db"),
    "user":     os.getenv("DB_USER",     "fitness_user"),
    "password": os.getenv("DB_PASS",     "fitness_pass"),
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def query(sql):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


# Weight data 
@app.route('/api/weight')
def weight():
    rows = query("""
        SELECT
            logged_date::text   AS date,
            weight_lbs,
            weight_7day_avg_lbs AS rolling_7d_avg,
            weight_change_lbs   AS change
        FROM public_marts.fct_daily_weight
        ORDER BY logged_date
    """)
    return jsonify(rows)


# Session data (for lift/volume/reps/sets charts)
@app.route('/api/sessions')
def sessions():
    rows = query("""
        SELECT
            logged_date::text                           AS date,
            day_type,
            exercise,
            side,
            CASE
                WHEN side IS NOT NULL
                THEN exercise || ' (' || side || ')'
                ELSE exercise
            END                                         AS exercise_label,
            max_weight_lbs                              AS max_weight,
            total_volume_lbs                            AS total_volume,
            total_reps,
            sets_completed
        FROM public_marts.fct_workout_session
        ORDER BY logged_date, exercise, side
    """)
    return jsonify(rows)


# Progress tracker (days since last weight or rep increase)
@app.route('/api/progress')
def progress():
    rows = query("""
        WITH session_pairs AS (
            SELECT
                logged_date,
                day_type,
                exercise,
                side,
                CASE WHEN side IS NOT NULL
                     THEN exercise || ' (' || side || ')'
                     ELSE exercise
                END                                         AS exercise_label,
                max_weight_lbs,
                total_reps,
                sets_completed,
                LAG(max_weight_lbs) OVER (
                    PARTITION BY exercise, side ORDER BY logged_date
                )                                           AS prev_weight,
                LAG(total_reps) OVER (
                    PARTITION BY exercise, side ORDER BY logged_date
                )                                           AS prev_reps,
                LAG(sets_completed) OVER (
                    PARTITION BY exercise, side ORDER BY logged_date
                )                                           AS prev_sets
            FROM public_marts.fct_workout_session
        ),
        progress_flags AS (
            SELECT
                logged_date,
                day_type,
                exercise,
                side,
                exercise_label,
                CASE
                    WHEN prev_weight IS NULL THEN TRUE  -- first session ever
                    WHEN max_weight_lbs > prev_weight THEN TRUE
                    WHEN total_reps    > prev_reps    THEN TRUE
                    WHEN sets_completed > prev_sets   THEN TRUE
                    ELSE FALSE
                END AS made_progress
            FROM session_pairs
        ),
        last_progress AS (
            SELECT
                exercise,
                side,
                exercise_label,
                day_type,
                MAX(logged_date) FILTER (WHERE made_progress = TRUE) AS last_progress_date,
                COUNT(*)                                               AS total_sessions
            FROM progress_flags
            GROUP BY exercise, side, exercise_label, day_type
        )
        SELECT
            exercise,
            side,
            exercise_label,
            day_type,
            last_progress_date::text,
            total_sessions,
            CURRENT_DATE - last_progress_date           AS days_since_progress
        FROM last_progress
        ORDER BY day_type, days_since_progress DESC NULLS LAST
    """)
    return jsonify(rows)


# Summary stats
@app.route('/api/stats')
def stats():
    weight_rows = query("""
        SELECT weight_lbs, logged_date::text AS date
        FROM public_marts.fct_daily_weight
        ORDER BY logged_date
    """)
    session_rows = query("""
        SELECT COUNT(DISTINCT logged_date) AS total_sessions,
               SUM(total_volume_lbs)      AS total_volume
        FROM public_marts.fct_workout_session
    """)
    stale_row = query("""
        WITH pairs AS (
            SELECT
                CASE WHEN side IS NOT NULL
                     THEN exercise || ' (' || side || ')'
                     ELSE exercise END AS exercise_label,
                logged_date,
                max_weight_lbs,
                total_reps,
                LAG(max_weight_lbs) OVER (PARTITION BY exercise, side ORDER BY logged_date) AS prev_weight,
                LAG(total_reps)     OVER (PARTITION BY exercise, side ORDER BY logged_date) AS prev_reps
            FROM public_marts.fct_workout_session
        ),
        progress_dates AS (
            SELECT
                exercise_label,
                logged_date
            FROM pairs
            WHERE prev_weight IS NULL
               OR max_weight_lbs > prev_weight
               OR total_reps > prev_reps
        ),
        last_prog AS (
            SELECT exercise_label, MAX(logged_date) AS last_progress_date
            FROM progress_dates
            GROUP BY exercise_label
        )
        SELECT exercise_label, CURRENT_DATE - last_progress_date AS days_since
        FROM last_prog
        ORDER BY days_since DESC NULLS LAST
        LIMIT 1
    """)

    start_weight = weight_rows[0]['weight_lbs']  if weight_rows else 0
    end_weight   = weight_rows[-1]['weight_lbs'] if weight_rows else 0
    start_date   = weight_rows[0]['date']        if weight_rows else ''

    return jsonify({
        "start_weight":    float(start_weight),
        "current_weight":  float(end_weight),
        "weight_change":   round(float(end_weight) - float(start_weight), 1),
        "total_sessions":  session_rows[0]['total_sessions'] if session_rows else 0,
        "total_volume":    float(session_rows[0]['total_volume'] or 0) if session_rows else 0,
        "start_date":      start_date,
        "most_stale":      stale_row[0]['exercise_label'] if stale_row else '',
        "most_stale_days": int(stale_row[0]['days_since'] or 0) if stale_row else 0,
    })



# Raw workout log (for the log table in dashboard)
@app.route('/api/log')
def log():
    rows = query("""
        SELECT
            logged_date::text   AS date,
            day_type,
            exercise,
            side,
            set_number,
            weight_lbs,
            reps,
            set_volume_lbs      AS volume
        FROM public_staging.stg_workout_log
        ORDER BY logged_date DESC, exercise, side, set_number
    """)
    return jsonify(rows)


if __name__ == '__main__':
    print("  Fitness API running at http://localhost:5000")
    print("   Open dashboard/index.html in your browser")
    app.run(debug=False, port=5000)
