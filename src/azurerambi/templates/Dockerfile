FROM python:3.11

WORKDIR /code
RUN pip install --upgrade pip
COPY . .
RUN pip install -e .

EXPOSE 8000

ENTRYPOINT ["gunicorn", "azurerambi.app:app"]
