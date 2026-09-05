# Workforce Analytics: Meridian Analytics Group

An end to end HR and workforce analytics project built for a fictional
mid-size company, Meridian Analytics Group. It covers the full pipeline
from raw data generation through transformation to a published
dashboard, and a lightweight app for exploring the data without
opening Tableau.

Live dashboard: **[link added once published to Tableau Public]**

## Why this project

I spent 8 years on the other side of workforce data: waiting on
headcount numbers, presenting turnover figures nobody questioned,
watching hiring pipelines stall without anyone asking why. This
project rebuilds that world end to end, from the raw employee and
hiring events up to the dashboard a People leader would actually look
at, so I could work through every layer myself: what the data looks
like before anyone touches it, what breaks when you join it, and what
questions the finished chart needs to answer.

## Architecture

```
generate_hr_data.py (Python + Faker)
        |
        v
dbt seeds (raw CSVs -> DuckDB "raw" schema)
        |
        v
dbt staging models (clean, type, derive one row per grain)
        |
        v
dbt mart models (headcount, turnover, time-to-fill, performance,
                  compensation equity)
        |
        +--> Streamlit app (quick exploration, in this repo)
        |
        +--> Tableau Public dashboard (the polished, shareable version)
```

## The dataset

Fully synthetic, generated with [Faker](https://faker.readthedocs.io/),
seeded for reproducibility. It simulates roughly 1,250 employees hired
over a 4.5 year window (January 2022 to August 2026) across 8
divisions and 19 departments, with realistic seasonal hiring slowdowns,
attrition, promotions, and compensation changes built into the
simulation logic rather than randomly scattered.

Raw tables (`data_generator/generate_hr_data.py` writes these to
`dbt_project/seeds/`):

| Table | Grain | What it captures |
|---|---|---|
| `raw_departments` | one row per department | department to division mapping |
| `raw_employees` | one row per employee | demographics, level, hire/termination dates, salary |
| `raw_requisitions` | one row per opened role | department, sourcing channel, open/close dates |
| `raw_hires` | one row per completed hire | links a requisition to the employee who filled it |
| `raw_terminations` | one row per termination event | voluntary/involuntary, reason, exit survey score |
| `raw_performance_reviews` | one row per quarterly review | rating 1 to 5 |
| `raw_compensation_history` | one row per salary change | new hire, merit, promotion |
| `raw_engagement_surveys` | one row per survey response | semi-annual engagement and satisfaction scores |

## The dbt project

`dbt_project/` follows the same staging-to-marts pattern as my
[dbt_project_mahmoud](https://github.com/Simba90m/dbt_project_mahmoud)
repo: a thin staging layer that cleans and types the raw sources one
to one, then mart models that do the actual joining and aggregation.

Staging models (`models/staging/`): one model per raw source, each
adding light cleanup (derived flags like `is_active`, computed
`tenure_days`, `days_to_fill`) without changing the grain.

Mart models (`models/marts/`):

- `mart_headcount_monthly`: month-end active headcount, hires, and
  terminations by department. Built from a generated date spine, since
  headcount at a point in time isn't a column anywhere in the raw
  data, it has to be derived.
- `mart_turnover_annual`: annual turnover rate by department, split
  into voluntary and involuntary, using average monthly headcount as
  the denominator.
- `mart_time_to_fill`: average and median days to fill a requisition,
  by department and sourcing channel.
- `mart_performance_engagement`: one row per employee, pairing average
  performance rating with average engagement and satisfaction scores.
- `mart_compensation_equity`: average and median salary by department,
  level, and gender, for compensation equity checks.

Data quality: 21 dbt tests (`not_null`, `unique`, `relationships`,
`accepted_values`) across the staging layer, plus a source freshness
check, all passing (`dbt test`).

DuckDB is the warehouse here instead of a hosted Postgres, so the
whole project runs locally with no cloud account needed to reproduce
it.

## The apps

**Streamlit** (`app/dashboard_app.py`): a quick, code-first look at the
marts, headcount trend by division, turnover by division, time to
fill by channel, and a compensation comparison by level and gender.
Useful for reviewing the data without opening Tableau.

**Tableau Public**: the polished, presentation-ready version of the
same marts, built for a non-technical audience, headcount and
attrition trend, hiring funnel efficiency, and a compensation equity
view. Link goes here once published.

## Running it locally

```bash
git clone https://github.com/Simba90m/workforce-analytics-meridian.git
cd workforce-analytics-meridian
pip install -r requirements.txt

# 1. generate the raw data
python data_generator/generate_hr_data.py

# 2. build the warehouse
cd dbt_project
dbt seed
dbt run
dbt test

# 3. explore it
cd ..
streamlit run app/dashboard_app.py
```

## Tech stack

Python (Faker for data generation, pandas/Streamlit/Plotly for the
exploration app), SQL, dbt (staging/marts modeling, testing, source
freshness), DuckDB, Tableau Public.

## Repo structure

```
data_generator/
    generate_hr_data.py       # writes raw CSVs to dbt_project/seeds/
dbt_project/
    dbt_project.yml
    macros/generate_schema_name.sql
    seeds/                     # raw_*.csv (generated, not hand-written)
    models/
        staging/               # stg_*.sql + sources.yml + schema.yml
        marts/                 # mart_*.sql + schema.yml
app/
    dashboard_app.py           # Streamlit companion app
requirements.txt
README.md
```
