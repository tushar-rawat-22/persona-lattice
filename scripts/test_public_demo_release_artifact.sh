#!/usr/bin/env bash
set -euo pipefail

workflow=".github/workflows/ci.yml"

require() {
  local needle="$1"
  if ! grep -Fq -- "$needle" "$workflow"; then
    printf 'missing public demo release artifact contract: %s\n' "$needle" >&2
    exit 1
  fi
}

require 'name: Publish verified public demo artifact'
require "if: github.event_name == 'push' && github.ref == 'refs/heads/main'"
require 'uses: actions/upload-artifact@v4'
require 'name: public-demo-${{ github.sha }}'
require 'path: apps/web/out'
require 'if-no-files-found: error'
require 'retention-days: 7'

publish_line="$(grep -n -F 'name: Publish verified public demo artifact' "$workflow" | cut -d: -f1)"
verify_line="$(grep -n -F 'name: Verify isolated public demo export' "$workflow" | cut -d: -f1)"

if [[ -z "$publish_line" || -z "$verify_line" || "$publish_line" -le "$verify_line" ]]; then
  echo 'public demo artifact must be published only after isolated export verification' >&2
  exit 1
fi

if grep -A10 -F 'name: Publish verified public demo artifact' "$workflow" | grep -Eq 'secrets\.|CLOUDFLARE|API_TOKEN|ACCOUNT_ID'; then
  echo 'public demo release artifact must not depend on deployment credentials' >&2
  exit 1
fi

printf 'public demo release artifact contract: PASS\n'
