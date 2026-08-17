"""
gunicorn_config.py — Gunicorn Configuration for Render Production Deployment
Used by: gunicorn -c gunicorn_config.py manage:application
"""

import os
import multiprocessing

# ─────────────────────────────────────────────────────────────────────────────
# Server Socket Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Bind to 0.0.0.0 and port from environment (Render sets PORT automatically)
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Canonical WSGI entry point (manage.py exposes application = create_app(...))
wsgi_app = "manage:application"

# Number of worker processes
# Render provides 1 CPU, so use 2-4 workers
workers = int(os.environ.get("WEB_CONCURRENCY", 3))

# Number of threads per worker for concurrent request handling
threads = 2

# Worker class: 'sync' for traditional, 'gevent' for async (sync is safer for Flask-SQLAlchemy)
worker_class = "sync"

# Maximum number of requests before worker restarts (memory leak prevention)
max_requests = 1000
max_requests_jitter = 100

# Worker timeout (requests taking longer than this are killed)
timeout = 60

# Graceful shutdown timeout
graceful_timeout = 30

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Log level
loglevel = "info"

# Access log format (for monitoring)
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Enable access logs (to stdout for Render log capture)
accesslog = "-"

# Error logs (to stdout)
errorlog = "-"

# ─────────────────────────────────────────────────────────────────────────────
# Process Naming & Security
# ─────────────────────────────────────────────────────────────────────────────

# Process name prefix (visible in ps output)
proc_name = "mjwebtech-api"

# ─────────────────────────────────────────────────────────────────────────────
# Request Handling
# ─────────────────────────────────────────────────────────────────────────────

# Ensure proper forwarded headers from reverse proxy (Render has one)
forwarded_allow_ips = "127.0.0.1"

# ─────────────────────────────────────────────────────────────────────────────
# Connection Pool Management
# ─────────────────────────────────────────────────────────────────────────────

# Preload application code for faster worker startup
preload_app = True

# Keep alive timeout for persistent connections
keepalive = 5

# ─────────────────────────────────────────────────────────────────────────────
# Development vs Production
# ─────────────────────────────────────────────────────────────────────────────

# Disable daemon mode (Render expects process to run in foreground)
daemon = False

# Redirect stdout/stderr to logs
capture_output = True
