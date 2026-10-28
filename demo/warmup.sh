#!/usr/bin/env bash
# Probudi Free Render servise pre nastupa (cold start FE često ~30 s).
set -euo pipefail

API="${NASALTER_API_URL:-https://ai4society-hackathon.onrender.com}"
WEB="${NASALTER_WEB_URL:-https://nasalter.onrender.com}"

echo "API  $API/health"
curl -sS -m 60 -o /dev/null -w "  %{http_code}  %{time_total}s\n" "$API/health"

echo "Web  $WEB/"
curl -sS -m 60 -o /dev/null -w "  %{http_code}  %{time_total}s\n" "$WEB/"
