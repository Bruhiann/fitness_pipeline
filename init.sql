CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS raw.workout_log (
    date        DATE,
    day_type    VARCHAR(20),
    exercise    VARCHAR(100),
    side        VARCHAR(10),
    set_number  INTEGER,
    weight_lbs  NUMERIC(6,2),
    reps        INTEGER
);

CREATE TABLE IF NOT EXISTS raw.weight_log (
    date        DATE,
    weight_lbs  NUMERIC(5,2)
);
```

**Step 3 — Start it back up:**
```
docker compose up -d 
