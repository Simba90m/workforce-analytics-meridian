with source as (
    select * from {{ source('raw', 'raw_engagement_surveys') }}
)

select
    survey_id,
    employee_id,
    survey_wave,
    survey_date,
    engagement_score,
    satisfaction_score
from source
