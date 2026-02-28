with sets as (
    select * from {{ ref('stg_workout_log') }}
),
session_agg as (
    select
        logged_date,
        day_type,
        exercise,
        side,
        is_unilateral,
        expected_sets,
        count(*)                                  as sets_completed,
        sum(reps)                                 as total_reps,
        max(weight_lbs)                           as max_weight_lbs,
        round(avg(weight_lbs), 2)                 as avg_weight_lbs,
        sum(set_volume_lbs)                       as total_volume_lbs,
        bool_and(reps between 5 and 8)            as all_sets_in_rep_range,
        count(*) = expected_sets                  as completed_all_sets
    from sets
    group by 1,2,3,4,5,6
)
select * from session_agg
order by logged_date, exercise, side nulls first