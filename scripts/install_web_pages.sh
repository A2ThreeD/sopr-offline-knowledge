#!/usr/bin/env bash
# SOPR Offline Knowledge
# Copyright (c) 2026 Aaron Morris / A2ThreeD.
# Publish the SOPR interface without restarting services.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PREPMASTER_ENV_FILE:-${SOPR_ENV_FILE:-$REPO_ROOT/config/sopr.env}}"
if [[ ! -f "$ENV_FILE" && -f "$REPO_ROOT/config/prepmaster.env" ]]; then
  ENV_FILE="$REPO_ROOT/config/prepmaster.env"
fi

source "$REPO_ROOT/scripts/load_env.sh"
load_sopr_env "$ENV_FILE"

install -d -m 0755 "$PREPMASTER_WEB_ROOT" "$PREPMASTER_ADMIN_ROOT" "$PREPMASTER_MAPS_ROOT" "$PREPMASTER_WEB_ROOT/kiwix-skin"
install -m 0644 "$REPO_ROOT/web/job-status.js" "$PREPMASTER_WEB_ROOT/job-status.js"
install -m 0644 "$REPO_ROOT/web/index.html" "$PREPMASTER_WEB_ROOT/index.html"
install -m 0644 "$REPO_ROOT/web/admin/index.html" "$PREPMASTER_ADMIN_ROOT/index.html"
install -m 0644 "$REPO_ROOT/web/maps/index.html" "$PREPMASTER_MAPS_ROOT/index.html"
install -m 0644 "$REPO_ROOT/web/kiwix-skin/viewer.js" "$PREPMASTER_WEB_ROOT/kiwix-skin/viewer.js"
echo "SOPR web pages installed."
