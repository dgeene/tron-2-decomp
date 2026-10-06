# Implementation milestones

Updated: 2026-10-05. Target agreed with owner: native Linux first, Windows next.

## Objective and completion criteria

Recover and understand the behavior of the installed TRON 2.0 game, gradually
reconstructing maintainable C++ that runs natively and reads the owner's game
assets. The existing Steam/Proton installation is the reference. A decompiler
dump is an intermediate research artifact, not a completed source port.

The initial approach is behaviorally compatible reconstruction, not a
byte-identical rebuild with the original compiler. Preserve original 32-bit
file formats and explicitly model integer widths and ABI boundaries. A modern
native build must not assume serialized pointers are host pointers.

## M0 — Reproducible baseline and tools

- [x] Confirm installed files and Killer App mod evidence without changing Steam files.
- [x] Establish Nix tool specification, lockfile, and optional local bootstrap.
- [x] Implement SHA-256 inventory and PE metadata/import/export reports.
- [x] Scaffold a portable C++20 CMake project with a useful REZ reader.
- [x] Add headless Ghidra import and catalog/pseudocode export scripts.
- [x] Verify Nix build, synthetic REZ tests, real archive catalogs, and Ghidra export.
- [x] Record baseline hashes, extracted-module provenance, and observed analysis counts.

Exit: another session can reproduce the inventory, build the tool, and reopen
the exact binary analysis projects without guessing paths or versions.

## M1 — Recover the module and archive boundaries

- [x] Catalog all eight installed REZ layers, including the backup.
- [x] Extract seven PE module candidates into separate, hash-identified local directories
      and verify each byte range and PE header.
- [ ] Confirm module discovery beyond the initial executable-extension candidate search.
- [ ] Analyze the engine and game modules; distinguish imports, exports, thunks,
      library routines, and game-specific code.
- [ ] Confirm archive precedence and actual module loads under Proton using
      traces; `launchcmds.txt` alone is not proof of precedence.
- [ ] Map startup, engine interfaces, game-shell entry points, class registration,
      resource lookup, and frame timing in `docs/` with addresses and confidence.
- [ ] Compare available mod/backed-up module variants. Treat the backups as
      candidates, not as a verified clean Steam release.
- [ ] Investigate officially released SDK headers/tools and document their
      provenance and permitted use before adopting any code.
- [ ] Evaluate the existing LithTech source candidate in `docs/SOURCES.md` for
      version matches and reusable interface knowledge before extensive recovery.

Exit: an evidence-backed module map and one selected, understood subsystem to
recover. Extend archive support only when actual files require it.

## M2 — First recovered subsystem in C++

- [ ] Select a small leaf subsystem from binary evidence (resource name lookup,
      archive overlay resolution, or a deterministic math routine).
- [ ] Record binary hash, RVA, signature hypotheses, callers, and edge cases.
- [ ] Recover readable C++, explain each inferred type, and create independent
      behavioral fixtures from the reference implementation where practical.
- [ ] Differentially verify normal and boundary cases against the original.
- [ ] Document discrepancies instead of adjusting tests to guessed behavior.

Exit: a tested reconstruction of actual game/engine behavior. The new archive
inspection utility is preparatory work and does not itself meet this milestone.

## M3 — Native Linux runtime and asset viewer

- [ ] Establish portable platform interfaces for files, time, windows, input,
      rendering, sound, and threading; keep Win32 calls out of game logic.
- [ ] Choose the rendering/window/audio libraries after the recovered interfaces
      are known; add them through Nix. Investigate D3D9 semantics in the engine.
- [ ] Load archive overlays with verified case-insensitive resource semantics.
- [ ] Decode a texture/model/world slice and render a reproducible scene.
- [ ] Record image comparisons and timing/input behavior against the original.

Exit: native Linux executable displays original owned assets and processes input
without Proton. This is an asset/runtime milestone, not yet a playable game.

## M4 — Playable single-player slice

- [ ] Recover movement, collision, camera, weapon/disc behavior, scripting,
      UI/HUD, sound, and a minimal level transition path.
- [ ] Make one agreed level playable end to end; compare against Proton captures.
- [ ] Recover save/load with explicit version handling and copied test saves.

Exit: repeatable native playthrough of that slice with documented limitations.

## M5 — Full single-player coverage and compatibility

- [ ] Recover remaining levels, enemies, cutscenes, progression, light cycles,
      menus, settings, and save compatibility.
- [ ] Decide whether to replace or wrap remaining proprietary middleware using
      observed interfaces; track video/audio fidelity separately.
- [ ] Validate the full campaign and mod/resource compatibility.
- [ ] Address resolution, focus, input, timing, and performance issues with
      reference cases rather than assumed fixes.

Exit: full campaign playable natively, with explicit feature coverage and
remaining differences. Multiplayer and dedicated-server behavior need a separate
coverage decision; they are not implicitly complete when single-player works.

## M6 — Windows and maintainability

- [ ] Build the same recovered C++ on Windows; implement platform adapters.
- [ ] Test graphics/input/audio and file handling on both systems.
- [ ] Package executables that locate the owner's assets without bundling them.
- [ ] Maintain provenance, regression cases, and an onboarding guide.

## Session handoff

Read `docs/BASELINE.md` and `docs/WORKFLOW.md`, then check this file. Reproduce only
the checks relevant to the next change. Keep binary inputs identified by SHA-256;
never merge addresses from different module versions without an explicit mapping.
When finishing a session, update the checklist, concrete results, unresolved
questions, and the next action. No recovered game function is verified yet.

Current handoff: **M0 complete; M1 in progress.** Build and fixture tests passed;
33 installed artifacts were fingerprinted, 19,713 layered resource entries were
cataloged, and seven PE variants were extracted. The engine analysis identified
6,372 functions and exported 25/25 selected pseudocode samples. See the baseline
for limitations. The Killer App client analysis identified 11,691 functions and
exported 25/25 samples. Next: map `SetMasterDatabase` registration
and analyze the object/effects modules, then verify actual loads under Proton.
