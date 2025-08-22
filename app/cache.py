import os
import sys
import redis
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import timedelta
import logging
import pandas as pd
import kagglehub
from io import StringIO

logging.basicConfig(filename='app.log', level=logging.INFO)
class Cache:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0, default_chunks = 100):
        self.files = {
    "airlines": "airlines.csv",
    "airports": "airports.csv",
    "flights": "flights.csv"
}
        self.cache_ttl = 300
        self.path = kagglehub.dataset_download("usdot/flight-delays")
        self.default_chunks = default_chunks
        try:
            client = redis.Redis(
				host=redis_host,
				port=redis_port,
				db=redis_db,
			)
            if client.ping():
                self.client = client
            else:
                logging.error("Connection established but Redis not responding to ping!")
        except redis.ConnectionError as ex:
            logging.error("Redis Connection Error: ", ex)
            sys.exit(1)
    
    def get_chunk_size(self, csv_path: Path) -> int:
        total_lines = sum(1 for _ in open(csv_path, "rb")) - 1
        chunk_size = total_lines // self.default_chunks
        return chunk_size
    
    def save_data_to_cache(self, name: str) -> bool:
        csv_filename = self.files[name]
        csv_path = Path(self.path) / csv_filename
        print(f"Reading {csv_path} (slow)")
        logging.info(f"Reading {csv_path} (slow)")
        chunk_size = self.get_chunk_size(csv_path)
        success = False
        total_rows = 0
        for i,chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size,low_memory=False)):
            cache_key = f"{name}_data_{i}"
            df = chunk
            json_data = df.to_json(orient='records', date_format='iso')
            state = self.client.setex(
			cache_key,
			self.cache_ttl,
			json_data,
		)
            if state:
                success = True
                total_rows += len(chunk)
                logging.info(f"Cached {name} chunk {i} ({len(chunk)} rows)")
        if success:
            logging.info(f"✅ Successfully cached {name} data (total {total_rows} rows)")
            print(f"✅ Successfully cached {name} data (total {total_rows} rows)")
        else:
            logging.error(f"❌ Failed to cache {name} data")
        
        return success

    def get_data_from_cache(self, name: str) -> Optional[pd.DataFrame] | None:
        pattern = f"{name}_data_*"
        keys = sorted(self.client.keys(pattern))
        dfs = []
        for key in keys:
            data = self.client.get(key)
            if data:
                df = pd.read_json(StringIO(data.decode("utf-8")), orient="records")
                dfs.append(df)
                
        if dfs:
            result = pd.concat(dfs, ignore_index=True)
            logging.info(f"Loaded {name} from cache ({len(result)} rows)")
            print(f"Loaded {name} from cache ({len(result)} rows)")
            return result
        else:
            logging.warning(f"No valid chunks found in cache for {name}")
            return None
        
    def get_or_load_data(self, name: str) -> Optional[pd.DataFrame]:
        df = self.get_data_from_cache(name)
        if df is not None:
            return df
        print(f"Data not in cache, loading {name} from CSV...")
        logging.info(f"Data not in cache, loading {name} from CSV...")
        if self.save_data_to_cache(name):
            return self.get_data_from_cache(name)
        else:
            logging.error(f"Failed to load and cache {name}")
            return None
        
   
