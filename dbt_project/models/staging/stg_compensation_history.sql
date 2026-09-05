with source as (
    select * from {{ source('raw', 'raw_compensation_history') }}
)

select
    comp_id,
    employee_id,
    effective_date,
    salary,
    change_reason
from source
