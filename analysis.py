import sqlite3
from database import DB_PATH


def main():
    connection = sqlite3.connect(DB_PATH)

    try:
        
        result = connection.execute("""
            SELECT
                COUNT(*) AS flight_count,
                AVG(ArrDelay) AS average_arrival_delay
            FROM flights
            WHERE Cancelled = 0
              AND Diverted = 0
              AND ArrDelay IS NOT NULL
        """)

        flight_count, average_delay = result.fetchone()

        print(f"Flights analyzed: {flight_count:,}")
        print(f"Average arrival delay: {average_delay:.2f} minutes")

        result = connection.execute("""
            SELECT COUNT(*)
            FROM flights
            WHERE Cancelled = 0
              AND Diverted = 0
              AND ArrDelay >= 15
        """)

        delayed_count = result.fetchone()[0]
        delayed_percentage = delayed_count / flight_count * 100

        print(f"Arrivals at least 15 minutes late: {delayed_count:,}")
        print(f"Percentage: {delayed_percentage:.2f}%")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
