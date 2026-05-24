#!/bin/bash
# Build React app for split-subdomain deploy (iweb + intapi).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/web"

API_URL="${VITE_API_BASE_URL:-https://intapi.bakerywala.cloud}"
WS_URL="${VITE_WS_BASE_URL:-wss://intapi.bakerywala.cloud}"

corepack enable 2>/dev/null || true
pnpm install

echo "Building with VITE_API_BASE_URL=$API_URL"
echo "Building with VITE_WS_BASE_URL=$WS_URL"

VITE_API_BASE_URL="$API_URL" VITE_WS_BASE_URL="$WS_URL" pnpm build
echo "Built → web/dist (serve on iweb.bakerywala.cloud)"
