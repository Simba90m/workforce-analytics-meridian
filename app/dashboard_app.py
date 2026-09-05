"""
Streamlit companion app for the Meridian Analytics Group workforce
dataset. This is a lightweight, code-first preview of the marts that
also power the Tableau Public dashboard: useful for exploring the data
quickly, or for anyone reviewing the repo without opening Tableau.

Run:
    streamlit run app/dashboard_app.py

Expects the dbt project to have already been built:
    cd dbt_project && dbt seed && dbt run
"""

import os

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "dbt_project", "hr_workforce_analytics.duckdb")

st.set_page_config(page_title="Meridian Workforce Analytics", layout="wide")


@st.cache_data
def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    headcount = con.execute("select * from marts.mart_headcount_monthly").df()
    turnover = con.execute("select * from marts.mart_turnover_annual").df()
    time_to_fill = con.execute("select * from marts.mart_time_to_fill").df()
    comp_equity = con.execute("select * from marts.mart_compensation_equity").df()
    con.close()
    return headcount, turnover, time_to_fill, comp_equity


headcount, turnover, time_to_fill, comp_equity = load_data()

st.title("Meridian Analytics Group: Workforce Overview")
st.caption(
    "Synthetic HR dataset, transformed with dbt, explored here in Streamlit and "
    "presented as a full dashboard on Tableau Public."
)

latest_month = headcount["month_start"].max()
current_headcount = headcount.loc[headcount["month_start"] == latest_month, "headcount"].sum()
trailing_12mo = headcount[headcount["month_start"] >= (pd.to_datetime(latest_month) - pd.DateOffset(months=12))]
trailing_hires = trailing_12mo["hires_count"].sum()
trailing_terms = trailing_12mo["terminations_count"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Current headcount", f"{current_headcount:,.0f}")
col2.metric("Hires, trailing 12 months", f"{trailing_hires:,.0f}")
col3.metric("Terminations, trailing 12 months", f"{trailing_terms:,.0f}")

st.subheader("Headcount over time, by division")
headcount_by_division = headcount.groupby(["month_start", "division"], as_index=False)["headcount"].sum()
fig_headcount = px.area(
    headcount_by_division,
    x="month_start",
    y="headcount",
    color="division",
    title="Company headcount, seeded January 2022",
)
st.plotly_chart(fig_headcount, use_container_width=True)

col4, col5 = st.columns(2)

with col4:
    st.subheader("Annual turnover rate by division")
    turnover_by_division = turnover.groupby(["division", "year"], as_index=False)["turnover_rate_pct"].mean()
    fig_turnover = px.bar(
        turnover_by_division,
        x="year",
        y="turnover_rate_pct",
        color="division",
        barmode="group",
        labels={"turnover_rate_pct": "Turnover rate (%)"},
    )
    st.plotly_chart(fig_turnover, use_container_width=True)

with col5:
    st.subheader("Time to fill by sourcing channel")
    ttf_by_channel = time_to_fill.groupby("source_channel", as_index=False).agg(
        avg_days_to_fill=("avg_days_to_fill", "mean"),
        requisitions_filled=("requisitions_filled", "sum"),
    )
    fig_ttf = px.bar(
        ttf_by_channel.sort_values("avg_days_to_fill"),
        x="source_channel",
        y="avg_days_to_fill",
        text="requisitions_filled",
        labels={"avg_days_to_fill": "Avg days to fill", "source_channel": "Sourcing channel"},
    )
    st.plotly_chart(fig_ttf, use_container_width=True)

st.subheader("Compensation by level and gender (active headcount)")
level_order = ["Junior", "Mid", "Senior", "Lead", "Manager", "Director"]
comp_equity["level"] = pd.Categorical(comp_equity["level"], categories=level_order, ordered=True)
fig_comp = px.box(
    comp_equity.sort_values("level"),
    x="level",
    y="avg_salary",
    color="gender",
    points=False,
    labels={"avg_salary": "Average salary by department (EUR)"},
)
st.plotly_chart(fig_comp, use_container_width=True)

st.caption(
    "Data is fully synthetic, generated for portfolio purposes. "
    "See data_generator/generate_hr_data.py for the generation logic and "
    "dbt_project/ for the staging and mart models."
)
