#!/bin/bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
NS3_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PATCH_FILE="$SCRIPT_DIR/nr_safety_fixes.patch"
NR_DIR="$NS3_ROOT/contrib/nr"

if [ ! -d "$NR_DIR" ]; then
    echo "Error: contrib/nr directory not found at $NR_DIR" >&2
    exit 1
fi

echo "Checking if 5G-LENA safety patches are applied in contrib/nr..."
cd "$NR_DIR"

if git apply --check --reverse "$PATCH_FILE" >/dev/null 2>&1; then
    echo ">> 5G-LENA safety patches are already applied."
else
    echo ">> Applying 5G-LENA safety patches to contrib/nr..."
    git apply "$PATCH_FILE"
    echo ">> Patches applied successfully."
fi
