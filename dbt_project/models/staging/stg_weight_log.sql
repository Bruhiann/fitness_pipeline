with source as (
    select * from {{ source('raw', 'weight_log') }}
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