#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
while IFS= read -r cmd; do
  echo "$(date -Iseconds) START $cmd"
  eval "$cmd"
  echo "$(date -Iseconds) DONE $cmd status=$?"
done < /tmp/nemotron_family_cmds.txt
