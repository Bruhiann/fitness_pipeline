
  create view "fitness_db"."public_staging"."stg_weight_log__dbt_tmp"
    
    
  as (
    with source as (
    select * from "fitness_db"."raw"."weight_log"
),
cleaned as (
    select
        date::date                as logged_date,
        weight_lbs::numeric(5,2)  as weight_lbs
    from source
    where date is not null
      and weight_lbs is not null
)
select * from cleaned
  );