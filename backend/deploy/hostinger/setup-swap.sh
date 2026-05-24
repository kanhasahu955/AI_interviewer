#!/bin/bash
# Add swap so Docker build (uv sync / ML wheels) doesn't OOM on small VPS.
# Run on the Hostinger VPS as root before docker compose build.
set -euo pipefail

SWAP_GB="${1:-4}"
SWAP_FILE="/swapfile"

if swapon --show | grep -q "$SWAP_FILE"; then
  echo "Swap already active at $SWAP_FILE"
  free -h
  exit 0
fi

echo "Creating ${SWAP_GB}G swap at $SWAP_FILE ..."
fallocate -l "${SWAP_GB}G" "$SWAP_FILE" || dd if=/dev/zero of="$SWAP_FILE" bs=1M count=$((SWAP_GB * 1024)) status=progress
chmod 600 "$SWAP_FILE"
mkswap "$SWAP_FILE"
swapon "$SWAP_FILE"
grep -q "$SWAP_FILE" /etc/fstab || echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab

echo "Done. Memory:"
free -h
