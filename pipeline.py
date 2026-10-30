import pandas as pd
import zipfile
import requests

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
BTS_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_"
    "1987_present_2025_1.zip"
)

ZIP_PATH = DATA_DIR / "bts_2025_01.zip"

def download_data():
    print("Downloading BTS flight data...")

    response = requests.get(BTS_URL, timeout=180)
    response.raise_for_status()

    ZIP_PATH.write_bytes(response.content)

    print(f"Download complete: {ZIP_PATH}")

def inspect_zip():
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        filename = archive.namelist()[0]

        with archive.open(filename) as file:
            header = file.readline().decode("utf-8-sig")
            print("Column names:")
            print(header)

def load_delta_data():
    columns = [
        "FlightDate",
        "Reporting_Airline",
        "Tail_Number",
        "Origin",
        "Dest",
        "DepDelay",
        "ArrDelay",
        "Flight_Number_Reporting_Airline",
        "Cancelled",
        "Diverted",
        "CRSDepTime",
        "CRSArrTime",
        "CRSElapsedTime",
    ]

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        filename = archive.namelist()[0]

        with archive.open(filename) as file:
            flights = pd.read_csv(file, usecols=columns)

    delta = flights.loc[
        flights["Reporting_Airline"] == "DL"
    ].copy()

    print(f"All airline records: {len(flights):,}")
    print(f"Delta records: {len(delta):,}")
    print(delta.head(5).to_string(index=False))

    return delta


def main():
    
    DATA_DIR.mkdir(exist_ok=True)
    print(f"Data folder ready: {DATA_DIR}")
    delta = load_delta_data()
    print("\nMissing values by column:")
    print(delta.isna().sum())

    print("\nFlight status counts:")
    completed = delta.loc[
        (delta["Cancelled"] == 0)
        & (delta["Diverted"] == 0)
    ].copy()

    print(f"\nCompleted, non-diverted flights: {len(completed):,}")
    print(
        "Missing arrival delays among these flights:",
        completed["ArrDelay"].isna().sum(),
    )
    print(f"Cancelled: {int(delta['Cancelled'].sum()):,}")
    print(f"Diverted: {int(delta['Diverted'].sum()):,}")
    output_path = DATA_DIR / "delta_2025_01.csv"
    delta.to_csv(output_path, index=False)

    print(f"\nSaved {len(delta):,} records to: {output_path}")

if __name__ == "__main__":
    main()
