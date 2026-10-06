#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo 'Usage (inside Nix analysis shell): scripts/analyze.sh BINARY [SAMPLE_LIMIT=25; 0=all]' >&2
    exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
binary=$(realpath -- "$1")
limit=${2:-25}
[[ $limit =~ ^[0-9]+$ ]] || { echo 'SAMPLE_LIMIT must be nonnegative' >&2; exit 2; }
command -v ghidra-headless >/dev/null || { echo 'Enter nix develop ./nix#analysis first.' >&2; exit 1; }
digest=$(sha256sum -- "$binary" | cut -d ' ' -f 1)
name=$(basename -- "$binary")
slug=$(printf '%s' "$name" | tr -c 'a-zA-Z0-9_-' '_')
project="${slug}_${digest:0:16}"
projects="$root/local/ghidra"
output="$root/local/analysis/$project"
mkdir -p "$projects" "$output"
export XDG_CONFIG_HOME="$root/local/config"
export XDG_CACHE_HOME="$root/local/cache"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
mode=(-import "$binary")
if [[ -e "$projects/$project.gpr" ]]; then
    # Preserve existing user labels/types. Re-run analysis to finish any interrupted import.
    mode=(-process "$name")
fi
rm -f -- "$output/COMPLETE"
ghidra-headless "$projects" "$project" "${mode[@]}" \
    -analysisTimeoutPerFile 600 -max-cpu 2 \
    -scriptPath "$root/ghidra" \
    -postScript ExportAnalysis.java "$output" "$limit" \
    -log "$output/headless.log" -scriptlog "$output/script.log"
# Ghidra may log a script failure while still returning zero.
[[ -f "$output/COMPLETE" ]] || { echo "Incomplete analysis/export: inspect $output" >&2; exit 1; }
printf 'Analysis written to %s\n' "$output"
