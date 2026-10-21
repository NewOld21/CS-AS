#!/usr/bin/env bash
# Chroma 1.5.3's published Rust image has bash, but no curl or Python.
set -euo pipefail
exec 3<>/dev/tcp/127.0.0.1/8000
printf 'GET /api/v2/heartbeat HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n' >&3
IFS= read -r -t 3 status <&3
[[ "$status" == HTTP/*' 200 '* ]]
