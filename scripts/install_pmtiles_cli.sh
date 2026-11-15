#!/usr/bin/env bash
# SOPR Offline Knowledge
# Copyright (c) 2026 Aaron Morris / A2ThreeD.
# Install the Protomaps archive extraction tool.

set -euo pipefail

if command -v pmtiles >/dev/null 2>&1; then
  exit 0
fi

version="1.31.2"
case "$(dpkg --print-architecture)" in
  arm64)
    architecture="arm64"
    checksum="f8bd47e7ea866863489cad588fbaf2f31f42e5821f7a03f009b3769f05801cb1"
    ;;
  amd64)
    architecture="x86_64"
    checksum="3ed7dbf4ec2e6dfe5e25b6f70d1ffc932729f93c86db353bf514dd71010a312f"
    ;;
  *)
    echo "Install pmtiles manually for this architecture before running Complete Setup." >&2
    exit 0
    ;;
esac

work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
archive="go-pmtiles_${version}_Linux_${architecture}.tar.gz"
echo "Installing Protomaps pmtiles $version for $architecture..."
curl -fSL --retry 3 --connect-timeout 15 \
  "https://github.com/protomaps/go-pmtiles/releases/download/v$version/$archive" \
  -o "$work_dir/$archive"
(
  cd "$work_dir"
  printf '%s  %s\n' "$checksum" "$archive" | sha256sum --check --status
  tar -xzf "$archive" pmtiles
)
install -m 0755 "$work_dir/pmtiles" /usr/local/bin/pmtiles
