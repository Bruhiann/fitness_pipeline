
  
    

  create  table "fitness_db"."public_marts"."fct_pr_tracker__dbt_tmp"
  
  
    as
  
  (
    -- models/marts/fct_pr_tracker.sql
-- Personal record (PR) tracker.
-- A PR is set when max_weight_lbs on a given date exceeds all previous dates
-- for that exercise + side combination.

with sessions as (
    select
        logged_date,
        exercise,
        side,
        max_weight_lbs,
        total_volume_lbs,
        total_reps
    from "fitness_db"."public_marts"."fct_workout_session"
),

running_max as (
    select
        logged_date,
        exercise,
        side,
        max_weight_lbs,
        total_volume_lbs,
        total_reps,

        max(max_weight_lbs) over (
            partition by exercise, side
            order by logged_date
            rows between unbounded preceding and 1 preceding
        )                                               as prev_best_weight_lbs,

        max(total_volume_lbs) over (
            partition by exercise, side
            order by logged_date
            rows between unbounded preceding and 1 preceding
        )                                               as prev_best_volume_lbs,

        rank() over (
            partition by exercise, side
            order by max_weight_lbs desc, logged_date asc
        )                                               as weight_rank

    from sessions
),

prs as (
    select
        logged_date,
        exercise,
        side,
        max_weight_lbs,
        prev_best_weight_lbs,
        total_volume_lbs,
        prev_best_volume_lbs,
        total_reps,
        weight_rank,

        -- Is this a weight PR?
        case
            when prev_best_weight_lbs is null then true   -- first time doing exercise
            when max_weight_lbs > prev_best_weight_lbs then true
            else false
        end                                             as is_weight_pr,

        -- Weight increase over previous best
        max_weight_lbs - coalesce(prev_best_weight_lbs, max_weight_lbs)
                                                        as weight_pr_increase_lbs

    from running_max
)

select * from prs
order by exercise, side nulls first, logged_date
  );
  