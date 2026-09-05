with source as (
    select * from {{ source('raw', 'raw_employees') }}
)

select
    employee_id,
    first_name,
    last_name,
    first_name || ' ' || last_name as full_name,
    gender,
    department_id,
    job_title,
    level,
    hire_date,
    termination_date,
    (termination_date is null) as is_active,
    location_city,
    location_country,
    employment_type,
    manager_id,
    base_salary,
    datediff('day', hire_date, coalesce(termination_date, current_date)) as tenure_days
from source
