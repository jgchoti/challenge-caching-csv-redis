# Redis Cache for Large CSV Processing

This project demonstrates how to use Redis as a caching layer for processing large CSV files efficiently. It showcases advanced Redis features including hash operations (`HSET`/`HGET`) for chunked data storage and optimized configuration for large datasets.

## Features

- **Chunked Data Processing**: Large CSV files are split into manageable chunks for efficient memory usage
- **Redis Hash Storage**: Uses `HSET`/`HGET` operations instead of simple `SET`/`GET` for better data organization
- **Memory-Optimized Configuration**: Custom Redis configuration for handling large datasets
- **Dockerized Environment**: Complete setup with Docker Compose for easy deployment
- **Performance Monitoring**: Built-in cache hit/miss metrics and timing analysis

## Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)

### Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/jgchoti/challenge-caching-csv-redis.git
   cd challenge-caching-csv-redis
   ```

2. **Build and start the containers**:

   ```bash
   # Build the application container
   docker-compose build

   # Start Redis with optimized configuration
   docker-compose up -d redis

   # Verify Redis is running
   docker-compose logs redis
   ```

## Configuration

### Redis Configuration for Large Data

The project includes a custom `redis.conf` optimized for large dataset processing:

```conf
# Memory management (1.5GB limit)
maxmemory 1610612736
maxmemory-policy allkeys-lru

# Enable persistence to prevent data loss
save 900 1
save 300 10
save 60 10000

# Performance optimizations for hash operations
hash-max-ziplist-entries 512
hash-max-ziplist-value 64

# Network optimizations for large data transfers
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
```

### Docker Compose Configuration

Memory limits are configured to handle large datasets:

```yaml
services:
  redis:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  app:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

## Running the Application

1. **Process the CSV data**:

   ```bash
   docker-compose run --rm app python main.py
   ```

2. **Monitor Redis performance**:

   ```bash
   # Check Redis memory usage
   docker stats redis_cache

   # Connect to Redis CLI for debugging
   docker-compose exec redis redis-cli
   ```

## Technical Architecture

### Hash-Based Chunking Strategy

Instead of storing entire datasets as single values, this implementation uses Redis hash operations:

```python
# Store data in chunks using HSET
cache_key = f"{dataset_name}_data"
for i, chunk in enumerate(chunks):
    json_data = chunk.to_json(orient='records')
    client.hset(cache_key, str(i), json_data)

# Retrieve data using HGETALL
cached_chunks = client.hgetall(cache_key)
for chunk_id, data in sorted(cached_chunks.items()):
    df_chunk = pd.read_json(StringIO(data), orient="records")
```

### Benefits of Hash Operations

- **Atomic Operations**: Each chunk is stored independently
- **Selective Retrieval**: Can retrieve specific chunks if needed
- **Better Memory Management**: Redis can handle hash operations more efficiently
- **Metadata Storage**: Easy to store chunk count and other metadata

## Example Performance Logs

### First Run (Cache Miss)

```
Reading /root/.cache/kagglehub/datasets/usdot/flight-delays/versions/1/flights.csv (slow)
Cached flights chunk 0 (58190 rows)
Cached flights chunk 1 (58190 rows)
...
=== Performance Metrics ===
Data loading time: 6.46 seconds
Computation time: 0.68 seconds
Total time: 7.14 seconds
```

### Subsequent Runs (Cache Hit)

```
=== Performance Metrics ===
Data loading time: 3.24 seconds
Computation time: 0.01 seconds
Total time: 3.25 seconds

=== Cache Metrics ===
Cache hits: 8
Cache misses: 3
```

## Dataset Analysis Results

The application performs analysis on flight delay data:

### Average Delay by Airline

```
Top 10 Airlines by Average Delay:
Southwest Airlines Co.        23.10 minutes
American Airlines Inc.        21.93 minutes
Delta Air Lines Inc.         18.27 minutes
United Air Lines Inc.        17.98 minutes
```

### Busiest Airports

```
Top 10 Busiest Airports:
Hartsfield-Jackson Atlanta Intl    18,059 flights
Chicago O'Hare International       14,463 flights
Los Angeles International          14,337 flights
```

## Memory Management Best Practices

### For Large Datasets (>1GB)

1. **Chunk Size Optimization**:

   ```python
   # Calculate optimal chunk size based on dataset
   total_rows = get_row_count(csv_file)
   chunk_size = max(1, total_rows // desired_chunks)
   ```

2. **Memory Monitoring**:

   ```python
   # Check Redis memory usage
   info = redis_client.info('memory')
   used_memory = info['used_memory_human']
   ```

3. **TTL Management**:
   ```python
   # Set appropriate expiration times
   client.expire(cache_key, 3600)  # 1 hour for large datasets
   ```

## Performance Comparison

| Operation    | Without Cache | With Cache | Improvement    |
| ------------ | ------------- | ---------- | -------------- |
| Data Loading | 6.46s         | 3.24s      | **50% faster** |
| Analysis     | 0.68s         | 0.01s      | **99% faster** |
| Total Time   | 7.14s         | 3.25s      | **55% faster** |

## Troubleshooting

### Common Issues

1. **Redis Memory Errors**:

   - Increase `maxmemory` in `redis.conf`
   - Check Docker memory limits
   - Monitor with `docker stats redis_cache`

2. **Connection Issues**:

   ```bash
   # Test Redis connectivity
   docker-compose exec redis redis-cli ping

   # Check container networking
   docker-compose exec app ping redis
   ```

3. **Data Retrieval Failures**:
   ```bash
   # Check cache contents
   docker-compose exec redis redis-cli
   > KEYS *
   > HKEYS flights_data
   ```

## Limitations and Considerations

### When Redis Cache is Ideal

- **Frequently accessed data** (high read-to-write ratio)
- **Complex computations** that benefit from caching results
- **Medium-sized datasets** (< 2GB) that fit comfortably in memory

### When to Consider Alternatives

- **Very large datasets** (> 10GB) that exceed available RAM
- **Write-heavy workloads** where cache invalidation is frequent
- **Simple data access patterns** where disk I/O is already fast

### Recommended Architecture for Massive Data

For datasets > 10GB, consider a hybrid approach:

- **Redis**: Cache frequently accessed aggregations and query results
- **Database**: Store full dataset (PostgreSQL, MongoDB)
- **File System**: Keep raw CSV files with columnar format (Parquet)

## Conclusion

This project demonstrates that Redis can significantly improve performance for large CSV processing when properly configured:

- **Hash operations** provide better organization than simple key-value storage
- **Memory management** is crucial for large dataset stability
- **Chunking strategies** enable processing of datasets larger than available RAM
- **Proper configuration** can handle multi-gigabyte datasets effectively

The 55% performance improvement shows the power of intelligent caching, but always consider your specific use case, data size, and access patterns when choosing caching strategies.
