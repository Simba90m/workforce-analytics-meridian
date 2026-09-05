-- One row per employee: average performance rating alongside average
-- engagement and satisfaction survey scores, for the "does engagement
-- track with performance" view.

with perf as (
    select employee_id, avg(rating) as avg_rating, count(*) as review_count
    from {{ ref('stg_performance_reviews') }}
    group by 1
),

eng as (
    select
        employee_id,
        avg(engagement_score) as avg_engagement_score,
        avg(satisfaction_score) as avg_satisfaction_score
    from {{ ref('stg_engagement_surveys') }}
    group by 1
)

select
    e.employee_id,
    e.department_id,
    d.department_name,
    d.division,
    e.level,
    e.is_active,
    round(p.avg_rating, 2) as avg_rating,
    p.review_count,
    round(en.avg_engagement_score, 2) as avg_engagement_score,
    round(en.avg_satisfaction_score, 2) as avg_satisfaction_score
from {{ ref('stg_employees') }} e
left join perf p on p.employee_id = e.employee_id
left join eng en on en.employee_id = e.employee_id
left join {{ ref('stg_departments') }} d on d.department_id = e.department_id
