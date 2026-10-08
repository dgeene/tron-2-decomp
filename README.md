# TRON 2.0 reconstruction workspace

Personal study and incremental C++ reconstruction of a licensed TRON 2.0 installation.
Target: **native Linux first, Windows second**. The existing Proton game is the
behavioral reference. This workspace is not yet a playable port.

Start with [the milestone plan](docs/MILESTONES.md) and
[the initial findings](docs/BASELINE.md).
Existing source and SDK research leads are recorded in [sources](docs/SOURCES.md).
The next milestone's [interface map](docs/INTERFACES.md) and
[Proton trace results](docs/RUNTIME_TRACING.md) are now available.

## Development environment

Dependencies come from the pinned Nix flake in `nix/`. Keeping the flake there
prevents Nix from copying game data, Ghidra projects, and tool caches into its
source store. Run commands below from this workspace root.

```sh
# With Nix already installed:
nix --extra-experimental-features 'nix-command flakes' develop ./nix

# Alternatively, install the pinned, workspace-local Linux Nix runtime:
./scripts/bootstrap-nix.sh
./scripts/nix.sh develop ./nix

# Add Ghidra and radare2 (larger first download):
./scripts/nix.sh develop ./nix#analysis
# The prompt now reads [tron:analysis]. Launch the GUI explicitly:
ghidra
```

The default shell includes a C++ compiler, CMake, Ninja, GDB, binutils,
Python with pefile, and inspection utilities. No global package installation is
required. See [the workflow](docs/WORKFLOW.md) for analysis and resuming work.

```sh
export TRON_GAME_DIR='/home/anon/.local/share/Steam/steamapps/common/Tron 2.0'
python scripts/inventory.py "$TRON_GAME_DIR" --out local/reports/installation.json
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
build/dev/reztool list "$TRON_GAME_DIR/gamep5.rez"
```

`reztool` is a native C++ archive inspection tool, the first small learning
project here. It catalogs REZ v1 files and extracts an explicitly named member.
It does not modify archives or implement the game engine.

## Workspace layout

| Path | Purpose |
| --- | --- |
| `docs/` | Milestones, evidence, format notes, and recovery workflow |
| `nix/` | Dependency specification and lockfile |
| `src/`, `tests/` | Authored portable C++ tools and synthetic tests |
| `scripts/`, `ghidra/` | Repeatable inventory and Ghidra analysis |
| `local/` | Ignored binary extracts, generated reports, Ghidra projects |
| `.tools/`, `build/` | Ignored local Nix runtime/cache and build outputs |

The Steam installation is read only input to these tools. Keep proprietary
binaries, assets, extracted modules, and raw decompiler output under `local/`,
outside future commits. Hashes, original code, and analysis notes belong in the
repository. No license for the original game is implied by this workspace.
