# Use the official Python image from the Docker Hub
FROM python:3.12.3-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gdal-bin libgdal-dev && \
    apt-get install -y build-essential

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_VERSION=3.6.2
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 5000 to the outside world
EXPOSE 5000

# Define the command to run the application
CMD ["python", "flask_app.py"]
