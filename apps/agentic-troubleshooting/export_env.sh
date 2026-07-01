#!/bin/bash

# Loads and exports all variables from a .env file.
# Can be used in two ways:
#   1. Sourced by other scripts:  source export_env.sh
#   2. Run directly for local testing: ./export_env.sh
#
# Accepts an optional path argument, defaults to .env in the same directory.
# Usage: source export_env.sh [path/to/.env]

load_env() {
    local env_file="${1:-$(dirname "${BASH_SOURCE[0]}")/.env}"

    if [ ! -f "$env_file" ]; then
        echo "Error: .env file not found at: $env_file"
        return 1
    fi

    while IFS= read -r line; do
        # Skip comments and blank lines
        [[ "$line" =~ ^# ]] && continue
        [[ -z "$line" ]] && continue

        # Strip surrounding quotes from value
        line=$(echo "$line" | sed 's/="/=/' | sed 's/"$//')
        export "$line"
    done < "$env_file"

    echo "Environment variables loaded from: $env_file"
}

# If run directly, call load_env immediately
# If sourced by another script, just make load_env available
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    load_env "$1"
fi