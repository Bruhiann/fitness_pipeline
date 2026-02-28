
  
    

  create  table "fitness_db"."public_marts"."fct_daily_weight__dbt_tmp"
  
  
    as
  
  (
    with base as (
    select * from "fitness_db"."public_staging"."stg_weight_log"
),
with_rolling as (
    select
        logged_date,
        weight_lbs,
        round(avg(weight_lbs) over (
            order by logged_date
            rows between 6 preceding and current row
        ), 2) as weight_7day_avg_lbs,
        weight_lbs - lag(weight_lbs) over (
            order by logged_date
        )     as weight_change_lbs
    from base
)
select * from with_rolling
order by logged_date
  );
  