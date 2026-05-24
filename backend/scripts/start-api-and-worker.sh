#!/bin/sh
# Run API + RQ worker in one container (for single free web service on Render etc.)
set -e
python -m app.jobs.worker &
exec /app/scripts/start-api.sh
