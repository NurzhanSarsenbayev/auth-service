#!/usr/bin/env bash
set -euo pipefail

echo "==> Stop containers"
make down >/dev/null || true

echo "==> Remove demo artifacts"
rm -rf .demo || true

echo "OK"
