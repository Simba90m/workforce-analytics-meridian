-- Annual turnover rate by department, split into voluntary and
-- involuntary, using average monthly headcount as the denominator.

with terms as (
    select
        e.department_id,
        extract(year from t.termination_date) as year,
        t.voluntary
    from {{ ref('stg_terminations') }} t
    join {{ ref('stg_employees') }} e on e.employee_id = t.employee_id
),

term_counts as (
    select
        department_id,
        year,
        count(*) as terminations,
        count(*) filter (where voluntary) as voluntary_terminations
    from terms
    group by 1, 2
),

avg_headcount as (
    select
        department_id,
        extract(year from month_start) as year,
        avg(headcount) as avg_headcount
    from {{ ref('mart_headcount_monthly') }}
    group by 1, 2
)

select
    a.department_id,
    d.department_name,
    d.division,
    a.year,
    round(a.avg_headcount, 1) as avg_headcount,
    coalesce(t.terminations, 0) as terminations,
    coalesce(t.voluntary_terminations, 0) as voluntary_terminations,
    round(coalesce(t.terminations, 0) / nullif(a.avg_headcount, 0) * 100, 1) as turnover_rate_pct,
    round(coalesce(t.voluntary_terminations, 0) / nullif(a.avg_headcount, 0) * 100, 1) as voluntary_turnover_rate_pct
from avg_headcount a
left join term_counts t
    on t.department_id = a.department_id and t.year = a.year
left join {{ ref('stg_departments') }} d
    on d.department_id = a.department_id
order by 1, 2
