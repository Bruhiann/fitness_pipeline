# Fitness ELT Pipeline

```
Raw CSVs → Python (extract_load.py) → Postgres (Docker)
                                           ↓
                              dbt: sources → staging → marts
                                           ↓
                              dashboard/index.html
```

## Stack
- **Python** + psycopg2 — extract & load CSVs
- **Postgres 15** via Docker — raw / staging / marts schemas
- **dbt-postgres** — all transformations
- **HTML + Chart.js** — dashboard (open in browser, no server needed)

---

## Quick Start

### 1. Start Postgres
```bash
docker compose up -d
# Wait ~10 seconds for healthcheck to pass
```

### 2. Install Python deps
```bash
pip install -r requirements.txt
```

### 3. Load CSVs into raw schema
```bash
python extract_load/extract_load.py
```

### 4. Run dbt transformations
```bash
cd dbt_project
dbt deps                          # no packages needed yet, but good habit
dbt run
dbt test                          # runs schema tests
```

### 5. Open dashboard
```bash
open dashboard/index.html         # macOS
# or just drag the file into your browser
```

---

## Project Structure

```
fitness_pipeline/
├── docker-compose.yml            # Postgres service
├── init.sql                      # Schema + table DDL
├── requirements.txt              # psycopg2 + dbt-postgres
│
├── data/
│   ├── workout_log.csv           # Your workout data → edit this
│   └── weight_log.csv            # Your body weight data → edit this
│
├── extract_load/
│   └── extract_load.py           # Reads CSVs, loads into raw.*
│
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml              # Postgres connection config
│   └── models/
│       ├── staging/
│       │   ├── sources.yml       # Points dbt at raw schema
│       │   ├── stg_weight_log.sql
│       │   └── stg_workout_log.sql
│       └── marts/
│           ├── schema.yml        # Tests
│           ├── fct_daily_weight.sql
│           ├── fct_workout_session.sql
│           └── fct_pr_tracker.sql
│
└── dashboard/
    └── index.html
```

---

## CSV Schema

### data/workout_log.csv
| Column | Type | Notes |
|---|---|---|
| date | DATE | YYYY-MM-DD |
| day_type | TEXT | pull / push / legs / abs |
| exercise | TEXT | lowercase |
| side | TEXT | left / right / (empty for bilateral) |
| set_number | INTEGER | 1 or 2 (incline chest press: 1 only) |
| weight_lbs | NUMERIC | 0 for bodyweight exercises |
| reps | INTEGER | target range: 5–8 |

### data/weight_log.csv
| Column | Type | Notes |
|---|---|---|
| date | DATE | YYYY-MM-DD |
| weight_lbs | NUMERIC | morning fasted recommended |

---

## Unilateral Exercises (tracked L + R separately)
- Single Arm Row
- Preacher Curl
- Lateral Raise
- Tricep Extension
- Calf Raise

---

## dbt Models

| Model | Schema | Type | Description |
|---|---|---|---|
| stg_weight_log | staging | view | Cleaned weight entries |
| stg_workout_log | staging | view | Cleaned sets + derived fields |
| fct_daily_weight | marts | table | Daily weight + 7-day rolling avg |
| fct_workout_session | marts | table | Per-exercise session aggregates |
| fct_pr_tracker | marts | table | PR history per exercise + side |

---

## Updating Your Data
1. Add rows to `data/workout_log.csv` or `data/weight_log.csv`
2. Re-run `python extract_load/extract_load.py` (truncates + reloads)
3. Re-run `dbt run`
4. Refresh `dashboard/index.html`

---

## Environment Variables (optional)
Override defaults via env vars:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=fitness_db
export DB_USER=fitness_user
export DB_PASS=fitness_pass
```
