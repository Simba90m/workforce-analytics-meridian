with source as (
    select * from {{ source('raw', 'raw_performance_reviews') }}
)

select
    review_id,
    employee_id,
    review_period,
    rating,
    review_date
from source
