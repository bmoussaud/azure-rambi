# Use Python 3.11 as the base image
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the default FastAPI port
EXPOSE 8002

# Command to run the FastAPI service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]