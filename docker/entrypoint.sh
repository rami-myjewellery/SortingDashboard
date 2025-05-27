#!/usr/bin/env bash
set -e

# 1️⃣  Flask scraper
python /app/python/scrape_dashboard_server.py &   # ✓ exact file name

# 2️⃣  Next.js standalone server
#   after the build stage we will copy  .next/standalone  into /app/box-cart-planner
node /app/web/.next/standalone/server.js &


wait -n
