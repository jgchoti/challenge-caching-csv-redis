# Redis Cache

This project demonstrates how to use Redis as a caching layer for a simple application that processes CSV files.

## Installation

1. **Install Redis**: Follow the instructions on the [Redis installation page](https://redis.io/docs/getting-started/installation/) to install Redis on your machine.
2. **Clone the repository**:

   ```bash
   git clone https://github.com/jgchoti/challenge-caching-csv-redis.git
   ```

3. **Navigate to the project directory**:

   ```bash
   cd challenge-caching-csv-redis
   ```

4. **Install dependencies**: Make sure you have Python and pip installed, then run:

```bash
   pip install -r requirements.txt
```

## Running the Application

1. **Start Redis server**: Open a terminal and run the following command to start the Redis server:
   ```bash
   docker run -d -p 6379:6379 -t redis:latest
   ```
2. **Run the application**: In a new terminal window, navigate to the project directory and run:

   ```bash
   python app/main.py

   ```

3. **Access the application**: Open your web browser and go to `http://localhost:5000` to interact with the application.

## Example Logs

When you run the application, you will see logs indicating whether the data was fetched from the cache or processed from the CSV file. Here’s an example of what the logs might look like:

```
WARNING:root:No valid chunks found in cache for flights
INFO:root:Data not in cache, loading flights from CSV...
INFO:root:Reading /Users/chotij/.cache/kagglehub/datasets/usdot/flight-delays/versions/1/flights.csv (slow)
INFO:root:Cached flights chunk 0 (58190 rows)
INFO:root:Cached flights chunk 1 (58190 rows)
...
INFO:root:✅ Successfully cached flights data (total 5819079 rows)
..
INFO:root:took 117.64 S to processes the CSV files
INFO:root:took 9.15 S to processes the CSV files and computes an aggregation
```

## Performance Notes

- **First run**: The first time you access the data, it will take longer as it processes the CSV file. For example, the first run might take around `117.64 seconds`.
- **Subsequent runs**: The next time you access the same data, it will be retrieved from the cache, significantly reducing the time taken to around `79.92 seconds`.  
  This demonstrates the efficiency of using Redis as a caching layer, improving performance for repeated data access.

## Conclusion

- Using Redis as a caching layer can significantly improve performance for applications that repeatedly access data, such as CSV files.
- Redis is not always the best tool for caching very large datasets. Since it is an in-memory store, large data can quickly consume available resources, leading to performance bottlenecks or high infrastructure costs.
- For large-scale scenarios, it’s often better to combine Redis with other storage strategies—such as chunking or a database designed for large volumes—while reserving Redis for frequently accessed subsets of data.
- This project illustrates the benefits of caching with Redis, but also highlights the importance of selecting the right tool and design patterns for the data size and usage patterns involved.
