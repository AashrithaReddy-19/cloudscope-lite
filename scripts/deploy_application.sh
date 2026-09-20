#!/usr/bin/env bash
set -euo pipefail
echo "This script does not create infrastructure. Copy the repository to the planned EC2 host, create .env there, then run: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"

