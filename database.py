from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

CSV_PATH = DATA_DIR / "delta_2025_01.csv"
DB_PATH = DATA_DIR / "flightripple.db"


def main():
    flights = pd.read_csv(CSV_PATH)

    connection = sqlite3.connect(DB_PATH)

    try:
        flights.to_sql(
            "flights",
            connection,
            if_exists="replace",
            index=False,
        )

        connection.commit()
        result = connection.execute(
            "SELECT COUNT(*) FROM flights"
        )
        row_count = result.fetchone()[0]

        print(f"SQL verified row count: {row_count:,}")
        print(f"Stored {len(flights):,} records in: {DB_PATH}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
