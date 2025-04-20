# Use Python 3.9 as base image
FROM python:3.9-slim

# Install Redis
RUN apt-get update && \
    apt-get install -y redis-server && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directory for user profiles
RUN mkdir -p profiles

# Expose ports for Redis and FastAPI
EXPOSE 6379 8000

# Copy and make the startup script executable
COPY start_chat.sh .
RUN chmod +x start_chat.sh

# Set the entrypoint
ENTRYPOINT ["./start_chat.sh"] 