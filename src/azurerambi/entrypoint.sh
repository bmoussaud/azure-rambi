#!/bin/sh
#gunicorn -c gunicorn.conf.py app:app
uvicorn  app:app --interface wsgi --host 0.0.0.0 --port 8000 --reload