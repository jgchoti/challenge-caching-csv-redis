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

logging.basicConfig(filename='app/app.log', level=logging.INFO)

class Cache:
    def __init__(self, redis_host: str = None, redis_port: int = None, redis_db: int = 0, default_chunks=100):
        import kagglehub
        import redis
        import logging
        import sys

        self.files = {
            "airlines": "airlines.csv",
            "airports": "airports.csv",
            "flights": "flights.csv"
        }
        self.cache_ttl = 300
        self.default_chunks = default_chunks

        self.path = kagglehub.dataset_download("usdot/flight-delays")

        self.redis_host = redis_host or os.environ.get("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.environ.get("REDIS_PORT", 6379))

        try:
            client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=redis_db,
                decode_responses=True  
            )
            client.ping()
            self.client = client
            print("✅ Redis reachable")
        except redis.ConnectionError as ex:
            logging.error("Redis Connection Error: %s", ex)
            print("❌ Cannot reach Redis:", ex)
            sys.exit(1)

    def get_chunk_size(self, csv_path: Path) -> int:
        total_lines = sum(1 for _ in open(csv_path, "rb")) - 1
        chunk_size = max(1, total_lines // self.default_chunks)
        return chunk_size
    
    def save_data_to_cache(self, name: str) -> bool:
        csv_filename = self.files[name]
        csv_path = Path(self.path) / csv_filename
        print(f"Reading {csv_path} (slow)")
        logging.info(f"Reading {csv_path} (slow)")
        chunk_size = self.get_chunk_size(csv_path)
        success = False
        total_rows = 0
        cache_key = f"{name}_data" 
        
        if self.client.exists(cache_key):
            self.client.delete(cache_key)
        
        for i, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False)):
            df = chunk
            json_data = df.to_json(orient='records', date_format='iso')
            try:
                result = self.client.hset(cache_key, str(i), json_data)
                success = True
                total_rows += len(chunk)
                logging.info(f"Cached {name} chunk {i} ({len(chunk)} rows)")
                print(f"Cached {name} chunk {i} ({len(chunk)} rows)")
            except redis.RedisError as e:
                logging.error(f"Failed to cache chunk {i} for {name}: {e}")
                return False
        
        if success:
            self.client.expire(cache_key, self.cache_ttl)
            logging.info(f"✅ Successfully cached {name} data (total {total_rows} rows)")
            print(f"✅ Successfully cached {name} data (total {total_rows} rows)")
        else:
            logging.error(f"❌ Failed to cache {name} data")
        
        return success

    def get_data_from_cache(self, name: str) -> Optional[pd.DataFrame]:
        cache_key = f"{name}_data"
        
        try:
            cached_chunks = self.client.hgetall(cache_key)
            print(f"Cached keys for {name}:", list(cached_chunks.keys()) if cached_chunks else "None")
            
            if not cached_chunks:
                logging.warning(f"No valid chunks found in cache for {name}")
                return None
            
            sorted_chunks = sorted(cached_chunks.items(), key=lambda item: int(item[0]))
            dfs = []
            
            for chunk_id, data in sorted_chunks:
                try:
                    df_chunk = pd.read_json(StringIO(data), orient="records")
                    dfs.append(df_chunk)
                except Exception as e:
                    logging.error(f"Failed to parse chunk {chunk_id} for {name}: {e}")
                    return None
            
            if not dfs:
                logging.warning(f"No valid data frames created for {name}")
                return None
                
            result = pd.concat(dfs, ignore_index=True)
            logging.info(f"Loaded {name} from cache ({len(result)} rows)")
            print(f"Loaded {name} from cache ({len(result)} rows)")
            return result
            
        except Exception as e:
            logging.error(f"Error retrieving {name} from cache: {e}")
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
        
    def get_query_from_cache(self, name: str, query_type: str, query_value: str) -> Optional[pd.DataFrame]:
        query_key = f"{name}:{query_type}:{query_value}"
        try:
            cached = self.client.hget(query_key, "results")
            if cached:
                self.client.incr("cache:hits")
                df = pd.read_json(StringIO(cached), orient="records")
                logging.info(f"Cache HIT for query {query_key} ({len(df)} rows)")
                return df
            else:
                self.client.incr("cache:misses")
                logging.info(f"Cache MISS for query {query_key}")
                return None
        except Exception as e:
            logging.error(f"Error retrieving query {query_key} from cache: {e}")
            self.client.incr("cache:misses")
            return None
        
    def save_query_to_cache(self, name: str, query_type: str, query_value: str, df: pd.DataFrame) -> bool:
        query_key = f"{name}:{query_type}:{query_value}"
        try:
            json_data = df.to_json(orient="records", date_format="iso")
            result = self.client.hset(query_key, "results", json_data)
            self.client.expire(query_key, self.cache_ttl)
            logging.info(f"✅ Cached query {query_key} ({len(df)} rows)")
            return True
        except Exception as e:
            logging.error(f"❌ Failed to cache query {query_key}: {e}")
            return False

    def get_or_load_query(self, name: str, query_type: str, query_value: str, compute_fn) -> pd.DataFrame:
        df = self.get_query_from_cache(name, query_type, query_value)
        if df is not None:
            return df
        df = compute_fn()
        self.save_query_to_cache(name, query_type, query_value, df)
        return df
    
    def clear_cache(self, name: str) -> int:
        key = f"{name}_data"
        if self.client.exists(key):
            self.client.delete(key)
            logging.info(f"Cleared cache for {name}")
            return 1
        return 0
            
    def get_cache_metrics(self) -> Dict[str, int]:
        hits = self.client.get("cache:hits")
        misses = self.client.get("cache:misses")
        return {
            "hits": int(hits) if hits else 0,
            "misses": int(misses) if misses else 0
        }
    
