#!/usr/bin/env bash
set -euo pipefail

personalattice_env_permissions_error=""

personalattice_validate_env_metadata() {
  local mode="$1"
  local owner="$2"
  local group="$3"

  personalattice_env_permissions_error=""
  if [[ "$mode" == "600" || "$mode" == "400" ]]; then
    return 0
  fi
  if [[ "$mode" == "640" || "$mode" == "440" ]]; then
    if [[ "$owner" == "root" && "$group" == "personalattice" ]]; then
      return 0
    fi
    personalattice_env_permissions_error="group-readable production environment files are permitted only as root:personalattice"
    return 1
  fi
  personalattice_env_permissions_error="production environment file must be mode 600/400, or 640/440 when owned by root:personalattice"
  return 1
}

personalattice_validate_env_file() {
  local path="$1"
  local mode
  local owner
  local group

  [[ -f "$path" ]] || {
    personalattice_env_permissions_error="production environment file not found: $path"
    return 1
  }

  if stat -c '%a' "$path" >/dev/null 2>&1; then
    mode="$(stat -c '%a' "$path")"
    owner="$(stat -c '%U' "$path")"
    group="$(stat -c '%G' "$path")"
  else
    mode="$(stat -f '%Lp' "$path")"
    owner="$(stat -f '%Su' "$path")"
    group="$(stat -f '%Sg' "$path")"
  fi

  personalattice_validate_env_metadata "$mode" "$owner" "$group"
}
