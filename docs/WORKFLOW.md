# Working and resuming

## Enter the environment

From the workspace root:

```sh
./scripts/nix.sh develop ./nix#analysis
export TRON_GAME_DIR='/home/anon/.local/share/Steam/steamapps/common/Tron 2.0'
```

`scripts/nix.sh` prefers an existing Nix installation. Without one, run
`scripts/bootstrap-nix.sh`: it fetches the x86_64 Linux v012 release of
[nix-portable](https://github.com/DavHau/nix-portable), checks the SHA-256 recorded
from the downloaded release, and keeps it in `.tools/`. That recorded digest is
a reproducibility pin, not an independently authenticated publisher signature.
The wrapper directs Nix caches into this workspace and selects the working
`bwrap` runtime; nix-portable v012's automatic `nix` runtime failed here with a
private mount namespace error. `NP_RUNTIME=proot` is an explicit alternative on
hosts without usable user namespaces (with possible performance costs).
Its portable fallback
disables Nix's nested build sandbox because this execution environment does not
permit that mount namespace; regular installed Nix keeps its normal settings.
This is distinct from the surrounding agent's execution permissions.

The bootstrap is optional; ordinary Nix can use the same `nix/flake.lock`. Initial
downloads require network access and several GB of disk. `aarch64-linux` is
declared in the flake but has not been tested; the bootstrap is x86_64 only.

Keep `flake.nix` and `flake.lock` in `nix/`, separate from proprietary data. To
intentionally update dependencies: `scripts/nix.sh flake update --flake ./nix`.
Record the new versions and rerun relevant checks.

## Inventory and archive inspection

```sh
python scripts/inventory.py "$TRON_GAME_DIR" --out local/reports/installation.json
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
build/dev/reztool list "$TRON_GAME_DIR/gamep5.rez"
mkdir -p local/modules/gamep5
build/dev/reztool extract "$TRON_GAME_DIR/gamep5.rez" CSHELL.DLL local/modules/gamep5/CSHELL.DLL
python scripts/inventory.py local/modules --out local/reports/modules.json
```

To catalog all installed archives and extract `.dll`, `.exe`, `.lto`, and `.fxd`
members whose payload starts with `MZ`, run:

```sh
python scripts/catalog.py "$TRON_GAME_DIR"
python scripts/inventory.py local/catalog --out local/reports/modules.json
```

This writes `local/catalog/archives.json`, per-archive TSV catalogs, and extracted
modules in folders named with the source archive's hash. Every extract is checked
against its source byte range, including on repeat runs. The subsequent PE
inventory validates whether each candidate really parses as a PE image. This
candidate search is extension-based, not a proof that no other resource embeds
executable code. Do not put the output directory inside the Steam installation.

Do not run the extraction command again over an existing file. Check its hash
and use the existing extract, or choose a new output directory. Inventory reports
contain complete hashes, PE section maps, entry points, imports, exports, version
strings, and parser warnings. COFF timestamps and version resources are labels,
not proof of origin. `pe_errors` is separate from nonfatal PE warnings.

## Ghidra

```sh
scripts/analyze.sh "$TRON_GAME_DIR/Lithtech.exe"
scripts/analyze.sh local/modules/gamep5/CSHELL.DLL
# Optional full pseudocode export; potentially much slower:
scripts/analyze.sh local/modules/gamep5/CSHELL.DLL 0
ghidra
```

Open a `.gpr` under `local/ghidra/` in the GUI. Close it before using headless
analysis. Each project name includes the filename and a SHA-256 prefix. The
wrapper reuses an existing import and its annotations; it does not use
`-overwrite`. Analysis has a ten-minute limit per binary and two worker CPUs.
Timed-out analyses retain the project for further work but do not produce a
completion marker. Individual function decompilation has a 30-second limit.

Outputs under `local/analysis/<project>/` include:

- `functions.tsv`: all functions Ghidra identified, with addresses and inferred signatures.
- `pseudocode/<address>.c`: selected raw decompiler results, unsuitable for direct compilation.
- `decompilation.tsv`: success/failure for this run's selected functions.
- `summary.txt`: binary hash, Ghidra version, architecture, analysis timeout, counts.
- `headless.log` and `script.log`: diagnostics.
- `COMPLETE`: the export script finished without the overall analysis timeout;
  it does not mean all functions were found, all samples succeeded, or the game is recovered.

The default sample is up to 25 functions, prioritizing binary entry points and
then address order. A limit of zero selects all identified nonexternal,
nonthunk functions plus entry points. Old pseudocode samples may remain after
reruns with smaller limits; use `decompilation.tsv` as this run's manifest.
Review warnings and per-function status even if the wrapper succeeds. Do not
equate Ghidra's auto-generated function count with total original functions or
percent completion. Automatic names/types are hypotheses.

This follows Ghidra's official [headless workflow](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md)
and [decompiler API](https://ghidra.re/ghidra_docs/api/ghidra/app/decompiler/DecompInterface.html).

## Record recovered behavior

For each subsystem, document:

1. Input module path, complete SHA-256, original VA and RVA.
2. Observed callers/callees, imports, constants, strings, and cross references.
3. Proposed type and function names, with confidence and alternatives.
4. Original behavior, edge cases, and a readable C++ implementation.
5. Independent validation against the reference, including any unresolved differences.

Use fixed-width integers for original fields. Keep host pointers separate from
32-bit serialized addresses. Model MSVC calling conventions and packing when
studying module interfaces. Do not infer the original source compiler version
solely from the PE linker version.

GDB in this environment is useful for native C++ tools. Debugging the Windows
game through Proton requires a separate setup with the appropriate Wine/Proton
debugging facilities; GDB being installed is not proof that this workflow works.
Dynamic tracing has not been configured by this initial scaffold.

## Future Git repository

This session does not initialize a repository. Before the first commit, review
the staged file list: include authored code, scripts, lockfiles, and notes;
exclude `local/`, `.tools/`, `build/`, binaries, assets, and raw decompiler output.
No license has yet been selected for newly authored project code.
