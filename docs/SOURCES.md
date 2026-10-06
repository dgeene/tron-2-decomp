# Research leads and provenance

Checked 2026-10-05. The current archive reader was written from observations of
the local files. No game or engine source from the following leads has been
copied into this workspace.

## Existing LithTech source candidate

The maintainer of [jsj2008/lithtech](https://github.com/jsj2008/lithtech) describes
the repository as based on an apparent Jupiter engine release and says it
includes TRON 2.0 game code. The same README describes modernization and
cross-platform support as unfinished work. This is a useful lead to investigate
before reconstructing large interfaces from scratch; it is not evidence that
the repository matches the installed binaries or is a finished native port.

Next steps: inspect the repository's provenance and per-component notices,
identify the TRON-specific version, and compare interface names, layouts,
constants, and representative functions against the hash-identified modules.
Record any files actually used and their exact revision. Do not infer an
engine-wide or game-wide license from the README's tentative description.

If matching source is useful, keep the original goal: an understandable native
Linux C++ implementation with independently checked behavior. Source-assisted
reconstruction can reduce effort; the binary baseline remains necessary to
identify mod changes and version differences.

## Editing tools and documentation

[TronFAQ's editing-tools repack announcement](https://tronfaq.blogspot.com/2011/07/tron-20-self-installing-editing-tools.html)
describes a bundle of the released editing tools, prefabs, documentation,
tutorials, and community additions. It may help document asset formats and
editor conventions. The repack has not been downloaded or run here, and its
contents have not yet been inventoried.

The installed Killer App readme also describes the author's experience making
the mod without game source. That historical account and the unrelated public
repository's claims should be investigated separately rather than treating
either as a definitive inventory of all source now available.

## Tool documentation used for this scaffold

- [nix-portable runtime and environment options](https://github.com/DavHau/nix-portable)
- [Ghidra headless analysis](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md)
- [Ghidra HeadlessScript API](https://ghidra.re/ghidra_docs/api/ghidra/app/util/headless/HeadlessScript.html)
- [Ghidra DecompInterface API](https://ghidra.re/ghidra_docs/api/ghidra/app/decompiler/DecompInterface.html)

The actual Nix package definitions used locally are identified by
`nix/flake.lock`; the tools are versioned independently of the game.
