#!/bin/bash
# Build on your laptop, copy image to VPS (when VPS build freezes / OOM).
# Usage:
#   ./deploy/hostinger/build-and-export.sh
#   scp interviewer-ai.tar.gz root@VPS:/tmp/
# On VPS:
#   docker load < /tmp/interviewer-ai.tar.gz
#   cd backend && docker compose -f docker-compose.hostinger.yml up -d
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
docker build --platform linux/amd64 -t interviewer-ai:latest .
docker save interviewer-ai:latest | gzip > interviewer-ai.tar.gz
echo "Created $(pwd)/interviewer-ai.tar.gz ($(du -h interviewer-ai.tar.gz | cut -f1))"
echo "scp interviewer-ai.tar.gz root@YOUR_VPS:/tmp/ && ssh root@YOUR_VPS 'docker load < /tmp/interviewer-ai.tar.gz'"
