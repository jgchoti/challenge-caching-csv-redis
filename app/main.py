import pandas as pd
from typing import Dict, Any, Optional
from cache import Cache
import logging
import time
import os

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))

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
    cache = Cache(redis_host=redis_host, redis_port=redis_port)

    
    t0 = time.time()

    flights_df = cache.get_or_load_data("flights")
    if flights_df is None:
        raise ValueError("Flights data failed to load from CSV or cache")
    airlines_df = cache.get_or_load_data("airlines")
    if airlines_df is None:
        raise ValueError("Airlines data failed to load from CSV or cache")
    airports_df = cache.get_or_load_data("airports")
    if airports_df is None:
        raise ValueError("Airports data failed to load from CSV or cache")


    t1= time.time()

    print("\n=== Computing Aggregations ===")

    print("\n--- Average Delay Analysis ---")
    avg_delays = cache.get_or_load_query(
        "flights",
        query_type="avg_delay",
        query_value="all_airlines",
        compute_fn=lambda: avg_delay_per_airline(flights_df, airlines_df)
    )
    
    print("\nTop 10 Airlines by Average Delay:")
    print(avg_delays.head(10))

    print("\n--- Airport Traffic  ---")
    total_flights = cache.get_or_load_query(
        "flights",
        query_type="total_flights",  
        query_value="all_airports",
        compute_fn=lambda: total_flights_per_airport(flights_df, airports_df)
    )
    print("\nTop 10 Busiest Airports:")
    print(total_flights.head(10))
    
    
    t2 = time.time()

    print(f"\n=== Performance Metrics ===")
    print(f"Data loading time: {(t1 - t0):.2f} seconds")
    print(f"Computation time: {(t2 - t1):.2f} seconds")
    print(f"Total time: {(t2 - t0):.2f} seconds")
    
   
    metrics = cache.get_cache_metrics()
    print(f"\n=== Cache Metrics ===")
    print(f"Cache hits: {metrics['hits']}")
    print(f"Cache misses: {metrics['misses']}")


if __name__ == "__main__":
    main()
