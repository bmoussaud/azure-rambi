#max_requests = 1000
#max_requests_jitter = 50

# Whether to send Django output to the error log 
capture_output = True
# How verbose the Gunicorn error logs should be 
loglevel = "debug"
# Access log - records incoming HTTP requests
#accesslog = "gunicorn.access.log"
# Error log - records Gunicorn server goings-on
#errorlog = "gunicorn.error.log"

bind = "0.0.0.0:8000"

worker_class = "uvicorn.workers.UvicornWorker"
workers = 3
