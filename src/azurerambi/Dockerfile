# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Creates a non-root user with an explicit UID and adds permission to access the /code folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /code
USER appuser

# Expose the default Flask port
EXPOSE 8000

# Command to run the application using gunicorn

ENTRYPOINT ["/code/entrypoint.sh"]