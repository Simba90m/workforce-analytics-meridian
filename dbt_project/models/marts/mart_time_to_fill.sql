-- Average and median time-to-fill for completed requisitions, by
-- department and sourcing channel. Feeds the hiring efficiency view.

select
    r.department_id,
    d.department_name,
    d.division,
    r.source_channel,
    count(*) as requisitions_filled,
    round(avg(r.days_to_fill), 1) as avg_days_to_fill,
    round(median(r.days_to_fill), 1) as median_days_to_fill
from {{ ref('stg_requisitions') }} r
join {{ ref('stg_departments') }} d on d.department_id = r.department_id
where r.status = 'Filled'
group by 1, 2, 3, 4
order by 1, 4
