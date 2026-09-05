with source as (
    select * from {{ source('raw', 'raw_requisitions') }}
)

select
    requisition_id,
    department_id,
    job_title,
    opened_date,
    closed_date,
    status,
    source_channel,
    datediff('day', opened_date, closed_date) as days_to_fill
from source
