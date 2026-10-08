#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
    echo 'Usage (in analysis shell): scripts/interfaces.sh BINARY [VA|xref:VA|define:VA ...]' >&2
    exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
binary=$(realpath -- "$1")
shift
digest=$(sha256sum -- "$binary" | cut -d ' ' -f 1)
name=$(basename -- "$binary")
slug=$(printf '%s' "$name" | tr -c 'a-zA-Z0-9_-' '_')
project="${slug}_${digest:0:16}"
[[ -f "$root/local/ghidra/$project.gpr" ]] || { echo 'Run scripts/analyze.sh on this binary first.' >&2; exit 1; }
output="$root/local/analysis/$project/interfaces"
mkdir -p "$output"
export XDG_CONFIG_HOME="$root/local/config"
export XDG_CACHE_HOME="$root/local/cache"
rm -f -- "$output/COMPLETE"
ghidra-headless "$root/local/ghidra" "$project" -process "$name" -noanalysis -readOnly \
    -scriptPath "$root/ghidra" -postScript ExportInterfaces.java "$output" "$@" \
    -log "$output/headless.log" -scriptlog "$output/script.log"
[[ -f "$output/COMPLETE" ]] || { echo "Evidence export failed: see $output" >&2; exit 1; }
