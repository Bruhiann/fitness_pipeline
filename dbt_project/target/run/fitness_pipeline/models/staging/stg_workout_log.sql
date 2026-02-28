
  create view "fitness_db"."public_staging"."stg_workout_log__dbt_tmp"
    
    
  as (
    -- models/staging/stg_workout_log.sql

with source as (
    select * from "fitness_db"."raw"."workout_log"
),

cleaned as (
    select
        date::date                          as logged_date,
        lower(trim(day_type))               as day_type,
        lower(trim(exercise))               as exercise,
        lower(trim(side))                   as side,         -- null for bilateral
        set_number::integer                 as set_number,
        weight_lbs::numeric(6,2)            as weight_lbs,
        reps::integer                       as reps,

        -- Derived: is this a unilateral exercise?
        case
            when lower(trim(exercise)) in (
                'single arm row',
                'preacher curl',
                'lateral raise',
                'tricep extension',
                'calf raise'
            ) then true
            else false
        end                                 as is_unilateral,

        -- Convenience: incline chest press has only 1 set
        case
            when lower(trim(exercise)) = 'incline chest press' then 1
            else 2
        end                                 as expected_sets,

        -- Volume for this set row
        (weight_lbs::numeric * reps::integer) as set_volume_lbs

    from source
    where date is not null
      and exercise is not null
      and set_number is not null
)

select * from cleaned
  );