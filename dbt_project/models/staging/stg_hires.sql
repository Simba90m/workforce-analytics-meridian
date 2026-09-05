with source as (
    select * from {{ source('raw', 'raw_hires') }}
)

select
    hire_id,
    requisition_id,
    employee_id,
    offer_date,
    start_date,
    source_channel,
    signing_bonus,
    datediff('day', offer_date, start_date) as offer_to_start_days
from source
