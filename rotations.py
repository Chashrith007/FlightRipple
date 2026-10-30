import airportsdata
import pandas as pd
import sqlite3

from database import DB_PATH

AIRPORTS = airportsdata.load("IATA")


def load_flights():
    connection = sqlite3.connect(DB_PATH)

    try:
        return pd.read_sql_query(
            "SELECT * FROM flights",
            connection,
        )
    finally:
        connection.close()


def build_rotations(flights, minimum_turn=30):
    flights = flights.copy()

    # Convert scheduled departure clocks, such as 1430, into minutes.
    clock = pd.to_numeric(flights["CRSDepTime"], errors="coerce")

    valid_clock = (
        clock.between(0, 2400)
        & (clock % 100 < 60)
        & (clock % 1 == 0)
    )

    minutes = (clock // 100) * 60 + clock % 100

    local_departure = (
        pd.to_datetime(flights["FlightDate"])
        + pd.to_timedelta(minutes.where(valid_clock), unit="m")
    )

    flights["departure_utc"] = pd.Series(
        pd.NaT,
        index=flights.index,
        dtype="datetime64[ns, UTC]",
    )

    # Each departure clock belongs to its origin airport's time zone.
    for airport, indices in flights.groupby("Origin").groups.items():
        timezone = AIRPORTS.get(airport, {}).get("tz")

        if timezone:
            flights.loc[indices, "departure_utc"] = (
                local_departure.loc[indices]
                .dt.tz_localize(
                    timezone,
                    ambiguous="NaT",
                    nonexistent="NaT",
                )
                .dt.tz_convert("UTC")
            )

    duration = pd.to_numeric(
        flights["CRSElapsedTime"], errors="coerce"
    )

    flights["arrival_utc"] = (
        flights["departure_utc"]
        + pd.to_timedelta(duration.where(duration > 0), unit="m")
    )

    # Conservatively exclude aircraft with an unplaceable scheduled leg.
    bad_tails = flights.loc[
        flights["departure_utc"].isna()
        | flights["arrival_utc"].isna(),
        "Tail_Number",
    ].dropna()

    flights = flights.loc[
        flights["Tail_Number"].notna()
        & ~flights["Tail_Number"].isin(bad_tails)
    ].copy()

    flights = flights.sort_values(
        ["Tail_Number", "departure_utc"]
    )

    # Shift gives each flight the preceding record for that aircraft.
    previous = flights.groupby("Tail_Number")[
        [
            "Dest",
            "arrival_utc",
            "ArrDelay",
            "Cancelled",
            "Diverted",
        ]
    ].shift(1)

    flights["inbound_arrival_delay"] = previous["ArrDelay"]

    flights["scheduled_ground_minutes"] = (
        flights["departure_utc"] - previous["arrival_utc"]
    ).dt.total_seconds() / 60

    # Keep consecutive, airport-matching, completed connections.
    eligible = (
        flights["Origin"].eq(previous["Dest"])
        & flights["Cancelled"].eq(0)
        & flights["Diverted"].eq(0)
        & previous["Cancelled"].eq(0)
        & previous["Diverted"].eq(0)
        & flights["DepDelay"].notna()
        & previous["ArrDelay"].notna()
        & flights["scheduled_ground_minutes"].between(0, 720)
    )

    # The aircraft must actually arrive before its next departure.
    eligible &= (
        flights["scheduled_ground_minutes"]
        + flights["DepDelay"]
        - previous["ArrDelay"]
    ).ge(0)

    pairs = flights.loc[eligible].copy()

    pairs["available_slack"] = (
        pairs["scheduled_ground_minutes"] - minimum_turn
    ).clip(lower=0)

    pairs["estimated_exposure"] = (
        pairs["inbound_arrival_delay"] - pairs["available_slack"]
    ).clip(lower=0)

    return pairs


if __name__ == "__main__":
    flights = load_flights()
    pairs = build_rotations(flights)

    print(f"Eligible consecutive flight pairs: {len(pairs):,}")
    print(
        "Pairs with estimated exposure:",
        f"{pairs['estimated_exposure'].gt(0).sum():,}",
    )

    columns = [
        "FlightDate",
        "Tail_Number",
        "Origin",
        "Dest",
        "inbound_arrival_delay",
        "scheduled_ground_minutes",
        "estimated_exposure",
        "DepDelay",
    ]

    print(
        pairs.sort_values(
            "estimated_exposure", ascending=False
        )[columns].head(5).to_string(index=False)
    )