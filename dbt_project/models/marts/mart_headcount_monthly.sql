-- Month-end headcount, hires, and terminations by department.
-- This is the primary source for the headcount trend and hiring vs
-- attrition charts on the dashboard.

with months as (
    select unnest(generate_series(date '2022-01-01', date '2026-08-01', interval '1 month')) as month_start
),

departments as (
    select * from {{ ref('stg_departments') }}
),

employees as (
    select * from {{ ref('stg_employees') }}
),

month_dept as (
    select m.month_start, d.department_id, d.department_name, d.division
    from months m
    cross join departments d
),

headcount as (
    select
        md.month_start,
        md.department_id,
        md.department_name,
        md.division,
        count(e.employee_id) as headcount
    from month_dept md
    left join employees e
        on e.department_id = md.department_id
        and e.hire_date <= (md.month_start + interval '1 month' - interval '1 day')
        and (e.termination_date is null or e.termination_date > (md.month_start + interval '1 month' - interval '1 day'))
    group by 1, 2, 3, 4
),

hires_per_month as (
    select department_id, date_trunc('month', hire_date) as month_start, count(*) as hires_count
    from employees
    group by 1, 2
),

terms_per_month as (
    select e.department_id, date_trunc('month', t.termination_date) as month_start, count(*) as terminations_count
    from {{ ref('stg_terminations') }} t
    join employees e on e.employee_id = t.employee_id
    group by 1, 2
)

select
    h.month_start,
    h.department_id,
    h.department_name,
    h.division,
    h.headcount,
    coalesce(hp.hires_count, 0) as hires_count,
    coalesce(tp.terminations_count, 0) as terminations_count
from headcount h
left join hires_per_month hp
    on hp.department_id = h.department_id and hp.month_start = h.month_start
left join terms_per_month tp
    on tp.department_id = h.department_id and tp.month_start = h.month_start
order by 1, 2
