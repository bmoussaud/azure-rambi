# Use the official Python image from Docker Hub
FROM python:3.11

# Set the working directory to /code
WORKDIR /code

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the default FastAPI port
EXPOSE 8000

# Set the entry point to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
