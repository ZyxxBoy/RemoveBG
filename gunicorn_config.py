"""Gunicorn configuration for production deployment."""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120  # rembg processing can take time

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Security
limit_request_body = 5242880  # 5 MB
