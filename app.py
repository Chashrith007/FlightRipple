import pandas as pd
import streamlit as st
import sqlite3
from database import DB_PATH
from rotations import load_flights, build_rotations



st.set_page_config(
    page_title="FlightRipple",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ FlightRipple")
st.subheader("Airline Delay Propagation Intelligence")

st.write(
    "Analyzing aircraft rotations to identify "
    "operational delays and downstream disruption risks."
)

connection = sqlite3.connect(DB_PATH)

try:
    result = connection.execute("""
        SELECT
            COUNT(*),
            AVG(ArrDelay),
            SUM(CASE WHEN ArrDelay >= 15 THEN 1 ELSE 0 END)
        FROM flights
        WHERE Cancelled = 0
          AND Diverted = 0
          AND ArrDelay IS NOT NULL
    """)

    flight_count, average_delay, delayed_count = result.fetchone()
    daily_delays = pd.read_sql_query("""
        SELECT
            FlightDate,
            COUNT(*) AS flight_count,
            AVG(ArrDelay) AS average_delay
        FROM flights
        WHERE Cancelled = 0
          AND Diverted = 0
          AND ArrDelay IS NOT NULL
        GROUP BY FlightDate
        ORDER BY FlightDate
    """, connection)
    jan10_status = pd.read_sql_query("""
        SELECT
            COUNT(*) AS total_flights,
            SUM(Cancelled) AS cancelled_flights,
            SUM(Diverted) AS diverted_flights
        FROM flights
        WHERE FlightDate = '2025-01-10'
    """, connection)

finally:
    connection.close()

delayed_percentage = delayed_count / flight_count * 100

st.subheader("Delta · January 2025")

col1, col2, col3 = st.columns(3)

col1.metric("Flights analyzed", f"{flight_count:,}")
col2.metric("Average arrival delay", f"{average_delay:.2f} min")
col3.metric("Arrivals ≥15 minutes late", f"{delayed_percentage:.2f}%")

st.caption(
    "Source: BTS Reporting Carrier On-Time Performance. "
    "Excludes cancelled and diverted flights. "
    "Average delay includes early arrivals."
)

st.subheader("Daily average arrival delay")
st.caption("Minutes behind schedule; negative values mean early arrivals.")
st.line_chart(
    daily_delays,
    x="FlightDate",
    y="average_delay",
)
st.subheader("Days with the highest average arrival delay")
worst_days = daily_delays.sort_values(
    "average_delay",
    ascending=False,
).head(5)
st.dataframe(worst_days, hide_index=True)
st.subheader("January 10: flight status")
st.dataframe(jan10_status, hide_index=True)
st.subheader("Aircraft delay exposure")

st.caption(
    "Estimated exposure assumes a 30-minute minimum turn. "
    "It is not proven delay attribution or a prediction."
)

rotation_pairs = build_rotations(load_flights())

st.metric("Eligible flight connections", f"{len(rotation_pairs):,}")

airports = sorted(rotation_pairs["Origin"].dropna().unique())

selected_airport = st.selectbox(
    "Connection airport",
    ["All airports"] + airports,
)

if selected_airport == "All airports":
    selected_pairs = rotation_pairs
else:
    selected_pairs = rotation_pairs.loc[
        rotation_pairs["Origin"] == selected_airport
    ]

display_columns = [
    "FlightDate",
    "Tail_Number",
    "Origin",
    "Dest",
    "inbound_arrival_delay",
    "scheduled_ground_minutes",
    "estimated_exposure",
    "DepDelay",
]

st.dataframe(
    selected_pairs.sort_values(
        "estimated_exposure", ascending=False
    )[display_columns].head(50),
    hide_index=True,
)

st.caption(
    "Top 50 connections by estimated exposure; delay values are minutes. "
    "The airport filter applies only to this table."
)