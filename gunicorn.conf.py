"""
Gunicorn configuration file.

This module defines the runtime settings for the Gunicorn WSGI server
that hosts the Flask/Socket.IO application in production.

Environment variables are supported to make the configuration flexible
across environments (local, staging, production).

Configuration options:
    workers (int): Number of worker processes. If not set via the
        environment, defaults to (2 * CPU cores + 1).
        Controlled by environment variable `GUNICORN_PROCESSES`.
    threads (int): Number of threads per worker. Defaults to 4.
        Controlled by environment variable `GUNICORN_THREADS`.
    bind (str): Address and port the server binds to. Defaults to
        '0.0.0.0:8080'.
        Controlled by environment variable `GUNICORN_BIND`.
    forwarded_allow_ips (str): IPs allowed to set proxy headers.
        Defaults to '*' (all).
    secure_scheme_headers (dict): Maps headers to their corresponding
        scheme (e.g., treating 'X-Forwarded-Proto: https' as HTTPS).

Example:
    Run with:
        gunicorn -c gunicorn.conf.py -k eventlet -w 1 wsgi:app
    One worker with eventlet for WebSocket support.
"""

import os
import multiprocessing

# Default: (2 * cores) + 1 workers, unless overridden
default_workers = (multiprocessing.cpu_count() * 2) + 1
workers = int(os.environ.get("GUNICORN_PROCESSES", default_workers))

threads = int(os.environ.get("GUNICORN_THREADS", "4"))
# timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8080")

FORWARDED_ALLOW_IPS = "*"
secure_scheme_headers = {"X-Forwarded-Proto": "https"}
