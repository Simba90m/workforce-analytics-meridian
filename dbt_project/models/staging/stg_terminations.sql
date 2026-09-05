with source as (
    select * from {{ source('raw', 'raw_terminations') }}
)

select
    termination_id,
    employee_id,
    termination_date,
    voluntary,
    reason,
    exit_survey_score
from source
