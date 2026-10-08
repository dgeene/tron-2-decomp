# Isolated Proton startup traces

Observed 2026-10-07 with the installed Proton Experimental, prefix version
`11.0-100`. This is a Windows reference run, not a native Linux game build.

The normal Steam game and its `compatdata/327740` prefix were not used as writable
runtime directories. A separate copy under `local/runtime/game` and separate
prefixes were used. Nix supplies `strace` and Xvfb; Proton itself is the user's
existing Steam installation, outside the Nix lock. Proton can update through
Steam, so record its version when reproducing results.

## What ran

The engine was launched directly with the archive list, windowed 800×600 output,
and audio disabled. Xvfb kept the test off the desktop. Wine's DLL-load log was
captured along with file-open traces. Temporary executable files were sampled
and hashed while the process ran. Only hashes matching extracted archive members
are treated as identified modules.

| Archive configuration | Loaded client shell | Loaded client resources |
| --- | --- | --- |
| Killer App after base/patch archives | Killer App `CSHELL.DLL`, hash `a4a0d800…` | `gamep6.REZ` `CRES.DLL`, hash `98b8b460…` |
| Killer App omitted | `gamep5.rez` `CSHELL.DLL`, hash `920046a0…` | Same `CRES.DLL` |
| Killer App before base/patch archives | `gamep5.rez` `CSHELL.DLL`, hash `920046a0…` | Same `CRES.DLL` |

Full hashes appear in `local/catalog/archives.json` and each trace's `trace.json`.
Wine also logged the corresponding temporary `cshell.dll` and `cres.dll` as
loaded native Windows modules. The reverse-order result verifies precedence for
this duplicate resource, consistent with the engine's head insertion of resource
trees and first-hit lookup. General cache/server-file precedence is still open.

All these runs stopped during graphics initialization. WineD3D reported that it
could not initialize an OpenGL context on the virtual display. Explicitly asking
for Mesa software rendering did not resolve it. Proton returned exit status zero
despite the game's startup failure, so exit status alone is not a success check.
These traces do not establish that the main menu rendered, that the effects or
object modules loaded, or that frame timing/gameplay is correct.

One trace sampled `cres.dll` before its write finished; that partial hash did not
match any archive member. A subsequent complete snapshot matched `gamep6.REZ`.
Snapshots are observations, not proof of loads by themselves; correlate them
with DLL-load lines and known complete module hashes.

## Reproduce

Enter `./scripts/nix.sh develop ./nix#analysis`, then:

```sh
export TRON_GAME_DIR='/home/anon/.local/share/Steam/steamapps/common/Tron 2.0'
mkdir -p local/runtime
if [ ! -e local/runtime/game ]; then
  cp -a --reflink=auto "$TRON_GAME_DIR" local/runtime/game
fi
python scripts/trace-proton.py \
  --proton '/home/anon/.local/share/Steam/steamapps/common/Proton - Experimental/proton' \
  --steam '/home/anon/.local/share/Steam' --seconds 60
```

Repeat with `--without-mod` or `--mod-first` to test archive selection. The
options are mutually exclusive. `--software-gl` adds a Mesa software-rendering
request and diagnostic logging. The helper bounds each run and stops only the
wineserver associated with its disposable prefix. It rejects a symlinked game
tree, so first prepare a real copy. On a filesystem without reflinks the game
copy consumes approximately its full installed size; it is kept for repeat runs.

Current helper versions use `local/runtime/compatdata-<configuration>`; the
first historical run used `local/runtime/compatdata`. Logs and snapshot binaries
are stored in a unique `local/runtime/logs/<configuration>-<run-id>/` directory.
The virtual-display log, Proton log, `files.log`, and `trace.json` must be read
together. Prefixes are reused within a configuration; remove or archive a
specific test prefix deliberately if a fresh-prefix experiment is needed.

Next runtime work: supply a working graphics context in this isolated setup,
then capture effects/object loading and a short controlled gameplay trace.
The original Steam/Proton setup remains the interactive reference for that work.
