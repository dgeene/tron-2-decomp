# M1: module and interface map

Updated 2026-10-07. Addresses below are **preferred-image VAs**, not runtime
addresses. Subtract `0x00400000` for engine RVAs, or `0x10000000` for the DLLs.
Full binary hashes are in [the baseline](BASELINE.md); local reports preserve
the hashes alongside every analysis. Names prefixed with “candidate” remain
research labels, not original symbols recovered from debug information.

## Module boundaries

| Module | Evidence-backed role | Analysis |
| --- | --- | --- |
| `TRON.exe` | MFC launcher; starts `Lithtech.exe` | PE inventory; launcher strings |
| `Lithtech.exe` | Platform/renderer, module loader, resource manager, frame dispatch | 6,372 automatic functions |
| Killer App `CSHELL.DLL` | Registers the client shell and consumes engine interfaces | 11,691 automatic functions |
| `OBJECT.LTO` from `gamep5.rez` | Registers the server shell; exposes game class definitions | 14,300 automatic functions, 40/40 initial samples |
| `CLIENTFX.FXD` from `gamep5.rez` | Effect registry and creation/property callbacks | 735 automatic functions, 40/40 initial samples |
| `CRES.DLL`, `SRES.DLL` | Resource DLLs; no named exports | Extracted and PE-parsed |
| `server.dll` | Standalone server engine interface | PE exports `CreateServer`, `DeleteServer` |

Imports, exports, thunks, and function signatures are recorded separately in the
PE inventories and Ghidra catalogs. Automatically named CRT/library functions
are not counted as recovered game logic. The function counts are discovery
results, not a coverage metric. Some real vtable targets were absent from the
automatic function table and needed explicit, temporary definitions.

Every one of the 19,713 archive resource headers was checked, regardless of its
extension. The same seven PE candidates were found. This checks resource starts;
it does not scan arbitrary interior offsets or decode compressed payloads.

## Loading and interface registration

| Engine VA | Evidence and interpretation |
| --- | --- |
| `0x00402a20` | `GetModuleHandleA`, then `LoadLibraryA`; on a first load, resolves and calls `SetMasterDatabase`; allocates an 8-byte module handle wrapper |
| `0x00447440` | Named export `SetMasterDatabase`; rejects null, own-local, or already-master cases; merges local registrations and switches the active database |
| `0x004475b0` | Candidate `GetMasterDatabase`; lazily allocates local bookkeeping/database and returns the selected database |
| `0x004295a0` | Client loader: locates/extracts `cshell.dll` and `cres.dll`, binds them, checks the client interface pointer |
| `0x00428ed0` | Object/server-resource loader: locates `object.lto` and `sres.dll`, validates setup and server interface availability |
| `0x00429460` | Resource-to-DLL-path helper, including a temporary-file path; Ghidra's inferred parameter list is unreliable here |

The binaries use named registration, rather than a `CreateClientShell` export.
Names such as `IClientShell.Default` and `ILTClient.Default` connect providers and
holders. Static initialization constructs these registrations; calling the
database export links the loaded module to the engine's registrations.

The engine bookkeeping pointer is at `0x005d5610`; the client equivalent is at
`0x10270640`. The engine allocates `0x24` bytes, with database values observed at
offsets `0`, `12`, and `24`. The candidate source describes local/master/active
tracked pointers, which is consistent with the binary's linked-list updates.
This is a structural correspondence, not a verified C++ class definition. Do
not substitute native 64-bit pointers into these 32-bit layouts.

## Verified version mismatch with the source candidate

Reference revision: `jsj2008/lithtech` at
`0eab18289bed72879eddb648d3311075b108cf46`. Its TRON-specific code is under
`NOLF2/*/TRON/`. The selected files and their hashes are listed in
[the reference manifest](references/lithtech.json).

| Interface | Installed binary evidence | Candidate source |
| --- | --- | --- |
| `IClientShell.Default` | Client initializer `0x10022610` passes `3`; engine holder `0x00410b70` also passes `3` | `sdk/inc/iclientshell.h` declares `4` |
| `IServerShell.Default` | Object initializer `0x10020a40` passes `3` | `sdk/inc/iservershell.h` declares `4` |
| `ILTClient.Default` | Client holder `0x100224d0` pushes `0x258` = `600` | Derived version is `4 + 100 × 4` = `404`, using `iltclient.h`, `iltcsbase.h`, and `ltmodule.h` |

The version values above were checked in raw instructions as well as pseudocode.
They rule out treating this candidate SDK as a drop-in ABI definition. The
source helps explain mechanisms and suggest names; each signature and vtable
slot still needs checking against the installed image. No source files from the
candidate are compiled into this project.

## Resource lookup and archive precedence

The file-manager implementation object is registered at `0x005d7890`. Its
constructor stores vtable `0x00589520`; its interface version argument is `0`.

| Engine VA | Observed behavior |
| --- | --- |
| `0x004a5820` | Opens resource trees in supplied order and inserts each successful tree at the front of the list; file-manager vtable offset `0x18` |
| `0x004a5a50` | Gets/caches a file identifier; normalizes names, hashes/searches them, then traverses resource trees; vtable offset `0x24` |
| `0x004a5d90` | Traverses trees until it can open the requested resource, then copies it to the supplied path; vtable offset `0x34` |
| `0x004c46e0` | Bounded copy, forced NUL terminator, uppercase conversion, and `/` to `\` conversion |

The linked-list insertion and traversal explain **later-added resource trees
winning**. Three controlled startup configurations independently verified that
rule for `CSHELL.DLL`: Killer App last loads the modded shell, Killer App omitted
loads the patch shell, and Killer App first loads the patch shell. See
[runtime tracing](RUNTIME_TRACING.md) for hashes, commands, and limitations.

This does not establish every loose-directory, cache, server-file, or case-folding
edge case. In particular, runtime temporary DLL snapshots can be captured while
a file is still being written; unmatched partial hashes are not extra module
versions.

## Game class and effects registration

`OBJECT.LTO!ObjectDLLSetup` at `0x100a2fb0` writes setup version `1`, stores its
second argument at `0x10344b28`, counts a linked list rooted at `0x1034fd88`,
allocates a 32-bit pointer array, copies each node's class pointer, and returns
that array and its count. The function exposes class metadata; its complete
class layout and ownership contract remain to be reconstructed.

`CLIENTFX.FXD!fxGetNum` at `0x100043d0` returns `17`. `fxGetRef` at `0x100043e0`
selects records containing names, flags, and callback addresses. Its apparent
extra output pointer may reflect a C++ aggregate-return convention; do not
adopt Ghidra's inferred prototype without checking the caller.

The client references and loads `ClientFX.fxd` in `0x10173a90`. The startup
traces stopped before this path and the server/object load were observed.

## Frame dispatch and timing anchors

Engine function `0x0040da20` is the main update-loop candidate. Its timer delta
path updates object-relative fields `+0xa20`, `+0xa24`, and `+0xa28`, and converts
the delta and absolute counter into floating-point fields `+0xa2c` and `+0xa30`.
The timer wrapper is `0x00484430`; a separate pacing path uses `0x00484400`,
`0x0041af80`, a sleep wrapper, and a bounded wait loop. Those timer contracts are
not yet validated dynamically.

`0x00411170` dispatches three client-shell calls through vtable byte offsets
`0x5c`, `0x60`, and `0x64`, with engine object updates between the second and
third. The main loop has a corresponding path when no current world shell is
active. These are candidates for pre-update/update/post-update callbacks based
on call order and comparison with the reference engine. The offsets are binary
evidence; those method names remain hypotheses. The public version-4 header's
method order is not the installed version-3 ABI.

## First reconstruction target (M2)

Select the resource-name normalization routine at engine VA `0x004c46e0`, RVA
`0xc46e0`, from engine hash
`63abeda1d8a003538811f12cecec91ef31ace229b95bb35e02042be24592a9ca`.

It is small enough to explain in C++ and directly useful for a native resource
loader. The observed non-null path copies up to the supplied capacity, writes
the final terminator, uppercases the result, then changes forward slashes to
backslashes. A null source writes an empty string. Capacity zero, overlapping
buffers, and non-ASCII locale behavior need explicit investigation rather than
being silently redefined. Validate ASCII names, mixed separators, empty/null
input, capacity one, truncation, and destination bounds against the original
machine code or a controlled original-process harness before marking M2 done.

## Reproducing the static evidence

Inside the Nix analysis shell:

```sh
python scripts/fetch-references.py
scripts/analyze.sh local/catalog/gamep5.rez_08139c408f11a64b/modules/OBJECT.LTO 40
scripts/analyze.sh local/catalog/gamep5.rez_08139c408f11a64b/modules/CLIENTFX.FXD 40
scripts/interfaces.sh "$TRON_GAME_DIR/Lithtech.exe" \
  0040da20 00411170 004475b0 define:004a5820 define:004a5a50 004a5d90 define:004c46e0
scripts/interfaces.sh local/catalog/Killer_App_Mod.REZ_2d5158c468f2fc2e/modules/CSHELL.DLL
scripts/interfaces.sh local/catalog/gamep5.rez_08139c408f11a64b/modules/OBJECT.LTO
scripts/interfaces.sh local/catalog/gamep5.rez_08139c408f11a64b/modules/CLIENTFX.FXD
```

`interfaces.sh` uses `-readOnly -noanalysis`. `define:VA` explicitly requests a
temporary function definition at a known code target missing from automatic
analysis; these changes are discarded when the project closes. `xref:VA`
selects functions referencing a specific address. Output includes `.asm`, `.c`,
string/reference tables, and a per-function status manifest. Old function files
remain across passes; `functions.tsv` describes the most recent pass.
