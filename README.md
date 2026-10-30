# FlightRipple
Airline delay analytics using Python, SQLite, and Streamlit.

## Overview
FlightRipple analyzes January 2025 BTS flight records reported
under Delta's DL carrier code. It combines SQL performance metrics,
daily trends, and an exploratory aircraft delay-exposure analysis.

## Dataset
Source: BTS Reporting Carrier On-Time Performance.
Official archives: https://transtats.bts.gov/PREZIP/

- All-carrier source records: 539,747
- Delta records: 76,306
- Completed, non-diverted Delta flights: 74,025
- Cancelled: 2,137
- Diverted: 144

This is a historical DL reporting-carrier slice, not all
Delta-marketed flights or Delta's complete worldwide operation.

## Findings
Among completed, non-diverted flights:
- Mean arrival delay: 5.22 minutes, including early arrivals.
- Arrivals at least 15 minutes late: 14,302 (19.32%).

January 10:
- 2,450 total records; 852 cancelled and 12 diverted.
- 1,586 completed, non-diverted flights.
- Mean arrival delay for those completed flights: 67.66 minutes.

These are descriptive findings; they do not establish causes.

## Aircraft connection analysis
Scheduled departures are converted from airport local time to UTC.
Scheduled flight duration determines scheduled arrival UTC.

Connections require:
- Consecutive records for the same aircraft tail number.
- Matching inbound destination and outbound origin.
- Neither flight cancelled or diverted.
- Reported inbound arrival and outbound departure delays.
- Scheduled ground time between 0 and 720 minutes.
- Actual inbound arrival no later than actual outbound departure.

Aircraft with missing or unusable scheduled timestamps are excluded.

Assumed minimum turn: 30 minutes.

Available slack = max(0, scheduled ground time - 30)
Estimated exposure = max(0, inbound arrival delay - available slack)

Exposure is an exploratory estimate, not causal attribution,
a validated prediction, or proven recoverable delay savings.

## Limitations
- The 30-minute turn assumption is not a verified Delta standard.
- Missing legs, month boundaries, and aircraft swaps affect linkage.
- Ambiguous/nonexistent local times are excluded.
- Scheduled arrival clocks are not independently cross-checked.
- Airport rankings and daily averages can reflect different flight mixes.
- Five synthetic unit tests check selected rules, not all real-world cases.

## Files
- pipeline.py: reads the BTS archive, filters DL, saves the CSV.
- database.py: loads the CSV into SQLite.
- analysis.py: calculates summary metrics with SQL.
- rotations.py: links aircraft flights and estimates exposure.
- app.py: displays the Streamlit dashboard.
- test_rotations.py: tests exposure, exclusions, time zones, and overnight flights.

## Run on the current Windows setup
Run these commands from the outer FlightRipple folder:

    .\FlightRipple\.venv\Scripts\python.exe .\pipeline.py
    .\FlightRipple\.venv\Scripts\python.exe .\database.py
    .\FlightRipple\.venv\Scripts\python.exe .\test_rotations.py
    .\FlightRipple\.venv\Scripts\python.exe -m streamlit run .\app.py

The current pipeline expects data\bts_2025_01.zip to exist.
For a fresh download, call the existing download_data() function
inside main() before load_delta_data(), then remove that call
after downloading to avoid fetching the archive on every run.

## Portfolio summary
Built a Python and SQLite pipeline analyzing 76,306 Delta flight
records, with a Streamlit dashboard for delay trends and aircraft
connection exposure. Added UTC-based flight sequencing and five
unit tests covering calculation logic and connection edge cases.

## Install on another Windows computer
Install Python first. From the project folder, run:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Follow the data preparation instructions above, using
.\.venv\Scripts\python.exe as the Python executable.

Launch the dashboard:

    .\.venv\Scripts\python.exe -m streamlit run .\app.py

Run the tests:

    .\.venv\Scripts\python.exe .\test_rotations.py