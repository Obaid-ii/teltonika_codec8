# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app
# Upgrade pip and setuptools to avoid compatibility issues before installing requirements
RUN pip install --upgrade pip setuptools wheel
# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# Create a requirements.txt if you don't have one already
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the container listens on port 5000 (if needed by the API)
EXPOSE 9025

# Run the Python script when the container launches
CMD ["python", "tcp.py", "--host", "0.0.0.0", "--port", "9025"]  # Replace 'tcp.py' with the main file that starts your app
