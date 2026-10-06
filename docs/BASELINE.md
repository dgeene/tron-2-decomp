# Installation baseline

Observed on 2026-10-05. Input directory:
`/home/anon/.local/share/Steam/steamapps/common/Tron 2.0`.
All installation access during this milestone was read only. No game process
was launched, and the Proton prefix was not changed.

## What the evidence establishes

- `TRON.exe` is the launcher. Its PE version resource identifies the product as
  the TRON 2.0 Launcher and the company as `TRON 2.0: Killer App Mod`. It imports
  MFC42 and contains references to `lithtech.exe -cmdfile launchcmds.txt`.
- `Lithtech.exe` is the engine analysis target: it imports Direct3D 9,
  DirectInput 8, WinMM, WinSock, and Win32 services, and contains references to
  `cshell.dll`, `cres.dll`, `sres.dll`, Bink, and sound-driver loading.
- The main images are 32-bit x86 PE files. Their linker version fields read 6.0.
  This does not establish the complete original compiler/toolchain.
- Killer App files are present, and the saved launch command requests
  `+mod Retail` and `Custom\Mods\Retail\Killer_App_Mod.REZ`. It also records
  2560×1440 output. This is saved configuration, not a runtime load trace.
- `KAModBackups/TRON.exe`, `KAModBackups/TRONSrv.exe`, and the backed-up
  `gamep6.rez` all differ from their installed counterparts. The `.text` sections
  of both launchers differ too; the changes are not confined to resources.
  Backup files are not assumed to be an independently verified retail baseline.
- Game code resides in archives as well as standalone files. PE parsing succeeds
  for all seven extracted module variants. Killer App's client shell and the
  patch client shell are both 2,502,656 bytes but differ at 112 byte positions.

The local generated inventory contains **33 installed artifacts** (including
archives) and **zero PE parse errors**. Parser warnings are retained in the JSON
and are distinct from parse errors. No PDBs have been obtained.

## Archive catalog

The native reader traversed all eight installed archives, including the backup:
19,713 resource entries in total. Counts include duplicate resources across
layers and must not be interpreted as unique assets.

| Source archive | Entries | Extracted PE candidates |
| --- | ---: | --- |
| `Custom/Mods/Retail/Killer_App_Mod.REZ` | 1,234 | `CSHELL.DLL` |
| `Engine.REZ` | 11 | — |
| `Game.rez` | 4,441 | — |
| `Game2.rez` | 7,050 | — |
| `KAModBackups/gamep6.rez` | 1 | `CRES.DLL` |
| `Sound.rez` | 6,856 | — |
| `gamep5.rez` | 119 | `CSHELL.DLL`, `OBJECT.LTO`, `CLIENTFX.FXD`, `SRES.DLL` |
| `gamep6.REZ` | 1 | `CRES.DLL` |

The candidate search checks `.dll`, `.exe`, `.lto`, and `.fxd` member extensions
and an `MZ` prefix, followed by PE parsing. It does not prove that other resource
types contain no embedded code. The saved launch command also mentions
`gamep3.rez` and `gamep4.rez`, which were absent from this inventory. Actual
missing-file handling and archive precedence are still to be traced.

## Binary identity and interface anchors

| Binary | SHA-256 |
| --- | --- |
| Installed `TRON.exe` | `803cb895837395517e3aecfa19939669c5f0c0d2188d9371b6a91cfcbbdf61eb` |
| Backup `TRON.exe` | `126e10394a19f8a290bfd1edada18f000421671353552f001d12b5503baf1657` |
| Installed `Lithtech.exe` | `63abeda1d8a003538811f12cecec91ef31ace229b95bb35e02042be24592a9ca` |
| Installed `server.dll` | `6472847879ce49c55273cdf85a22bd2eee45fcd27b4c5f2b8b737da979d61009` |
| Killer App `CSHELL.DLL` | `a4a0d800bd5697637e5df27c861ab71b84dad7051839c9ef28d0546c4c703309` |
| Patch `CSHELL.DLL` | `920046a07fb4aaae4ceb64558743f0828381c1ab2327e6b2aa637f632ea25509` |
| Patch `OBJECT.LTO` | `0c0c308c76f8f9384964a1466e45d88d0d34d94afaa27b5c1507193596e058dc` |
| Patch `CLIENTFX.FXD` | `04e13d5fdf5b236d84c8ac501b1852eb6682c8fad139287039f940a8ebaed030` |

These are original preferred-image addresses; DLLs may be relocated at runtime.

| Binary | Image base | Entry VA | Selected export RVA |
| --- | --- | --- | --- |
| `TRON.exe` | `0x00400000` | `0x0040cf6c` | — |
| `Lithtech.exe` | `0x00400000` | `0x0056ba62` | `LTGetILTMemory`: `0x42d50`; `SetMasterDatabase`: `0x47440` |
| Both `CSHELL.DLL` variants | `0x10000000` | `0x101d444d` | `SetMasterDatabase`: `0x4e450` |
| `OBJECT.LTO` | `0x10000000` | `0x1026a339` | `ObjectDLLSetup`: `0xa2fb0`; `SetMasterDatabase`: `0x107180` |
| `CLIENTFX.FXD` | `0x10000000` | `0x10021f78` | `fxGetNum`: `0x43d0`; `fxGetRef`: `0x43e0` |

The only named export in each client shell is `SetMasterDatabase`. Recovering
the registration/interface mechanism behind that export is a better next step
than assuming the client exposes a conventional `CreateClientShell` export.
The object and effects module roles are inferred from their exports and names;
their full contracts are not reconstructed.

## Reproduction artifacts

- `local/reports/installation.json`: installed hashes and PE descriptions.
- `local/catalog/archives.json`: archive hashes, counts, module offsets/sizes,
  extracted paths, and module hashes.
- `local/catalog/*/members.tsv`: complete per-archive catalogs.
- `local/reports/modules.json`: extracted module PE imports/exports and versions.
- `local/ghidra/`: hash-identified persistent projects.
- `local/analysis/`: generated function catalogs, pseudocode samples, and logs.

These are intentionally ignored by future Git commits. The authored tools and
this evidence summary are retained for reproducibility.

## Validation and limits

The C++ tool built with Nix GCC 16.2.0 and passed CTest. Its synthetic suite covers
listing/extraction, nested directories, refusal to overwrite, missing members,
and twelve malformed-input cases including cycles and out-of-bounds ranges.
All real extracted modules were byte-checked against the source archive spans.
The Nix flake evaluated successfully for the host's x86_64 Linux shells.

Ghidra uses version 12.1.2 from the pinned nixpkgs revision. Its PE analysis warns
that Windows system DLLs are not imported into the project, and the engine
analysis reported two invalid-PNG data detections. These are retained as
analysis limitations rather than silently discarded. Missing PDB information
means source-level names and types must be recovered through further evidence.

The engine's initial automatic analysis completed without its overall timeout,
identifying **6,372 functions** and successfully exporting **25 of 25** selected
pseudocode samples. Its language/compiler specification is
`x86:LE:32:default` / `windows`. These counts measure this analysis pass, not the
number of original source functions or completion of the reconstruction.

The Killer App client shell also completed without the overall timeout,
identifying **11,691 functions** and exporting **25 of 25** selected samples.
Both projects were saved successfully. Other extracted modules are cataloged
but have not yet been analyzed in Ghidra.

No native game runtime, rendering backend, recovered C++ game function, Proton
debugging workflow, or Windows build has been completed. Archive traversal and
PE parsing validate this initial tooling; they are not gameplay validation.

## Next session

Inspect the engine and client `SetMasterDatabase` routines and their cross
references, documenting the registration ABI with hash/RVA evidence. Analyze
`OBJECT.LTO` and `CLIENTFX.FXD` next. Then trace the original process under Proton
to confirm active module hashes and archive precedence before choosing the first
subsystem for reconstruction.
Before extensive manual recovery, evaluate the existing source candidate in
[the research notes](SOURCES.md) for version and interface matches.
