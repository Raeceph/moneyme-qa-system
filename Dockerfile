# Use Python 3.12 slim image as the base
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install build dependencies, install Python packages, then remove build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/vector_store

# Make the entry point script executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port that the application will run on
EXPOSE 8000

# Use the entry point script
ENTRYPOINT ["/entrypoint.sh"]