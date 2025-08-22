# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ .

# Expose port if needed (optional)
EXPOSE 8000

# Default command to run your app
CMD ["python", "main.py"]
