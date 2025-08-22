import pandas as pd
from typing import Dict, Any, Optional
from cache import Cache
import logging
import time

def avg_delay_per_airline(flights_df, airlines_df ):
    merged_df_airline = flights_df.merge(
    airlines_df,
    left_on="AIRLINE",
    right_on="IATA_CODE",
    how="left" 
    )
    return merged_df_airline.groupby("AIRLINE_y")["DEPARTURE_DELAY"].mean().sort_values(ascending=False)
   
def total_flights_per_airport(flights_df, airports_df):
    merged_df_airport = flights_df.merge(
    airports_df,
    left_on="ORIGIN_AIRPORT",
    right_on="IATA_CODE",
    how="left" 
    )
    return (
    merged_df_airport
    .groupby("AIRPORT")["FLIGHT_NUMBER"]
    .count()
    .sort_values(ascending=False)
    )
    
def main():
    cache = Cache()
    
    t0 = time.time()

    flights_df = cache.get_or_load_data("flights")
    airlines_df = cache.get_or_load_data("airlines")
    airports_df = cache.get_or_load_data("airports")

    t1= time.time()

    #  average delay per airline, 
    avg = avg_delay_per_airline(flights_df, airlines_df)
    print(avg)
    #total flights per airport
    total = total_flights_per_airport(flights_df, airports_df)
    print(total)

    t2 = time.time()
    total_process = t1 - t0
    logging.info(f"took {total_process:.2f} S to processes the CSV files")
    print(f"took {total_process:.2f} S to processes the CSV files")
    total_compute = t2-t1
    logging.info(f"took {total_compute:.2f} S to processes the CSV files and computes an aggregation ")
    print(f"took {total_compute:.2f} S to computes an aggregation ")


if __name__ == "__main__":
    main()
