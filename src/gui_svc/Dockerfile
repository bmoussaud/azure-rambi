# Base image: using Microsoft Container Registry devcontainers image to avoid current Docker Hub 503 outage.
# You can override at build time: docker build --build-arg BASE_IMAGE=python:3.11-slim ... once Docker Hub is healthy.
# Later, pin to a digest for reproducibility (e.g., python:3.11.8-slim-bookworm@sha256:<digest>). 
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

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

# Set the GITHUB_SHA, GITHUB_JOB, GITHUB_ACTOR, and GITHUB_RUN_NUMBER environment variables
ARG GITHUB_SHA
ARG GITHUB_JOB
ARG GITHUB_ACTOR
ARG GITHUB_RUN_NUMBER
ENV GITHUB_SHA=${GITHUB_SHA}
ENV GITHUB_JOB=${GITHUB_JOB}
ENV GITHUB_ACTOR=${GITHUB_ACTOR}
ENV GITHUB_RUN_NUMBER=${GITHUB_RUN_NUMBER}

# Expose the default Flask port
EXPOSE 8000

# Command to run the application using gunicorn

ENTRYPOINT ["/code/entrypoint.sh"]