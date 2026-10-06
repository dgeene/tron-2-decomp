#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if command -v nix >/dev/null 2>&1; then
    exec nix --extra-experimental-features 'nix-command flakes' "$@"
fi
if [[ ! -x "$root/.tools/nix-portable" ]]; then
    echo 'Nix is unavailable. Run ./scripts/bootstrap-nix.sh first.' >&2
    exit 1
fi
export NP_LOCATION="$root/.tools"
export NP_GIT="$(command -v git)"
export XDG_CACHE_HOME="$root/.tools/cache"
# v012's automatic "nix" runtime can fail for develop with a relocated store.
# Bubblewrap works on this host; callers can explicitly choose proot if needed.
export NP_RUNTIME="${NP_RUNTIME:-bwrap}"
# Nested Nix build namespaces are unavailable in some rootless containers.
# This affects Nix build isolation only; the caller's execution permissions apply.
exec "$root/.tools/nix-portable" nix --option sandbox false "$@"
