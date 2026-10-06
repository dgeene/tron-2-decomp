#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    echo 'This optional bootstrap is pinned for x86_64 Linux. Use an existing Nix installation on other hosts.' >&2
    exit 1
fi
mkdir -p "$root/.tools"
target="$root/.tools/nix-portable"
expected=b409c55904c909ac3aeda3fb1253319f86a89ddd1ba31a5dec33d4a06414c72a
if [[ ! -f "$target" ]]; then
    trap 'rm -f -- "$target.download"' EXIT
    curl -fL --retry 3 https://github.com/DavHau/nix-portable/releases/download/v012/nix-portable-x86_64 -o "$target.download"
    printf '%s  %s\n' "$expected" "$target.download" | sha256sum -c -
    mv -- "$target.download" "$target"
fi
printf '%s  %s\n' "$expected" "$target" | sha256sum -c -
chmod +x "$target"
"$root/scripts/nix.sh" --version
