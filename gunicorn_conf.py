# gunicorn_conf.py

# Gunicorn configuration file
import multiprocessing

# Socket Path
bind = "0.0.0.0:8000"

# Worker Options
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging Options
loglevel = "debug"
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"

# Reload code on change (for development)
reload = True

# Maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Process Name
proc_name = "moneyme_qa_api"

# Timeout
timeout = 120
