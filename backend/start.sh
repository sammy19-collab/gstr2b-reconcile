#!/bin/bash
set -e
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete. Starting server..."
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
