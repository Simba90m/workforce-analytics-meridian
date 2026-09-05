-- Current active headcount's salary by department, level, and gender.
-- Powers the compensation equity view (average and median pay gap
-- checks across the same level and department).

select
    d.department_name,
    d.division,
    e.level,
    e.gender,
    count(*) as employee_count,
    round(avg(e.base_salary), 0) as avg_salary,
    round(median(e.base_salary), 0) as median_salary
from {{ ref('stg_employees') }} e
join {{ ref('stg_departments') }} d on d.department_id = e.department_id
where e.is_active
group by 1, 2, 3, 4
order by 1, 3
