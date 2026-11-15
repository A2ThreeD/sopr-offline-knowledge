#!/usr/bin/env bash
# SOPR Offline Knowledge
# Copyright (c) 2026 Aaron Morris / A2ThreeD.
# Kiwix content downloader for the SOPR project.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PREPMASTER_ENV_FILE:-${SOPR_ENV_FILE:-$REPO_ROOT/config/sopr.env}}"
if [[ ! -f "$ENV_FILE" && -f "$REPO_ROOT/config/prepmaster.env" ]]; then
  ENV_FILE="$REPO_ROOT/config/prepmaster.env"
fi
URL_FILE="${PREPMASTER_ZIM_URL_FILE:-$REPO_ROOT/config/kiwix-zim-urls.txt}"
CUSTOM_URL_FILE="${PREPMASTER_ZIM_CUSTOM_URL_FILE:-$REPO_ROOT/config/kiwix-zim-urls.custom.txt}"
QUICK_TEST_FILE="$REPO_ROOT/config/kiwix-zim-urls.quick-test.txt"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo $0"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing config file: $ENV_FILE"
  exit 1
fi

if [[ ! -f "$URL_FILE" ]]; then
  echo "Missing URL manifest: $URL_FILE"
  exit 1
fi

# shellcheck source=./load_env.sh
source "$REPO_ROOT/scripts/load_env.sh"
load_sopr_env "$ENV_FILE"

PROFILE="${PREPMASTER_ZIM_PROFILE:-essential}"
WIKIPEDIA_OPTION="${PREPMASTER_WIKIPEDIA_OPTION:-top-mini}"
ZIM_MODE="${PREPMASTER_ZIM_MODE:-full}"

DOWNLOAD_LIBRARY_DIR="${PREPMASTER_ZIM_INSTALL_DIR:-$KIWIX_LIBRARY_DIR}"
DOWNLOAD_WIKIPEDIA_DIR="${PREPMASTER_WIKIPEDIA_INSTALL_DIR:-$DOWNLOAD_LIBRARY_DIR}"

if [[ "$ZIM_MODE" == "quick-test" ]]; then
  if [[ ! -f "$QUICK_TEST_FILE" ]]; then
    echo "Missing quick-test manifest: $QUICK_TEST_FILE"
    exit 1
  fi

  echo "Using quick-test Kiwix manifest..."
  URL_FILE="$QUICK_TEST_FILE"
elif [[ "$ZIM_MODE" == "custom" ]]; then
  if [[ ! -f "$CUSTOM_URL_FILE" ]]; then
    echo "Missing custom manifest: $CUSTOM_URL_FILE"
    exit 1
  fi

  echo "Using saved custom Kiwix manifest..."
  URL_FILE="$CUSTOM_URL_FILE"
else
  echo "Building Kiwix ZIM manifest from kiwix-categories.yaml..."
  python3 "$REPO_ROOT/scripts/build_kiwix_zim_manifest.py" \
    --source "$REPO_ROOT/catalog/kiwix-categories.yaml" \
    --output "$URL_FILE" \
    --profile "$PROFILE" \
    --wikipedia-options "$REPO_ROOT/catalog/wikipedia.yaml" \
    --wikipedia-choice "$WIKIPEDIA_OPTION"
fi

install -d -m 0755 "$KIWIX_LIBRARY_DIR"
install -d -m 0755 "$DOWNLOAD_LIBRARY_DIR"
install -d -m 0755 "$DOWNLOAD_WIKIPEDIA_DIR"
install -d -m 0755 "$DOWNLOAD_LIBRARY_DIR/.sopr-download-tmp"
install -d -m 0755 "$DOWNLOAD_WIKIPEDIA_DIR/.sopr-download-tmp"

python3 "$REPO_ROOT/scripts/download_zim_batch.py" \
  "$URL_FILE" "$KIWIX_LIBRARY_DIR" "$DOWNLOAD_LIBRARY_DIR" "$DOWNLOAD_WIKIPEDIA_DIR" \
  "${PREPMASTER_ZIM_DOWNLOAD_JOBS:-3}" \
  --mirror "${PREPMASTER_ZIM_CATALOG_URL:-https://cdimage.debian.org/mirror/kiwix.org/zim/}"

link_roots=("$DOWNLOAD_LIBRARY_DIR")
if [[ "$DOWNLOAD_WIKIPEDIA_DIR" != "$DOWNLOAD_LIBRARY_DIR" ]]; then
  link_roots+=("$DOWNLOAD_WIKIPEDIA_DIR")
fi

for root in "${link_roots[@]}"; do
  if [[ "$root" == "$KIWIX_LIBRARY_DIR" ]]; then
    continue
  fi
  while IFS= read -r zim_path; do
    file_name="$(basename "$zim_path")"
    link_path="$KIWIX_LIBRARY_DIR/$file_name"
    if [[ ! -e "$link_path" && ! -L "$link_path" ]]; then
      ln -s "$zim_path" "$link_path"
    fi
  done < <(find "$root" -maxdepth 1 -type f -name '*.zim' | sort)
done

if command -v kiwix-manage >/dev/null 2>&1; then
  "$REPO_ROOT/scripts/rebuild_kiwix_library.sh"
fi

echo "ZIM sync complete in $DOWNLOAD_LIBRARY_DIR"
