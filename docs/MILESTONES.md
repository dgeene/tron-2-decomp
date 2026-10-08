# Implementation milestones

Updated: 2026-10-07. Target agreed with owner: native Linux first, Windows next.

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
- [x] Check the header of every resource, independent of filename extension.
- [x] Analyze engine, client, object, and effects modules; record imports,
      exports, thunks, and automatic function catalogs separately.
- [x] Verify early client/resource DLL loading in isolated Proton traces.
- [x] Verify duplicate client-shell archive precedence by reversing archive order.
- [x] Map startup, interface registration, class/effect registration, resource
      lookup, and frame-dispatch anchors with addresses and confidence.
- [x] Compare client-shell variants and installed/backed-up PE sections. Backups
      remain candidates, not a verified clean Steam release.
- [ ] Resolve virtual-display OpenGL initialization; trace effects/object loading
      and actual frame timing after successful graphics initialization.
- [ ] Investigate officially released SDK headers/tools and document their
      provenance and permitted use before adopting any code.
- [x] Evaluate the existing LithTech source candidate at a pinned revision.
      Installed client/server shell version 3 differs from candidate version 4;
      installed ILTClient version 600 differs from candidate version 404.

Exit: an evidence-backed module map and one selected, understood subsystem to
recover. Extend archive support only when actual files require it.

## M2 — First recovered subsystem in C++

- [x] Select resource-name normalization, engine VA `0x004c46e0` / RVA `0xc46e0`.
- [x] Record binary hash, signature hypotheses, caller, and edge cases in
      `docs/INTERFACES.md`.
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

Current handoff: **M0 complete; M1 mapping delivered, runtime follow-up remains.**
Read `docs/INTERFACES.md` and `docs/RUNTIME_TRACING.md` for the 2026-10-07 results.
Object/effects analyses completed (14,300 and 735 automatic functions); both
exported 40/40 initial samples. Interface evidence is exported read-only, with
explicit temporary definitions for missed vtable targets. All-resource discovery
and its synthetic regression test passed. The interactive Nix shell now shows
`[tron:analysis]` and launch guidance.

Three archive-order configurations confirmed client-shell selection by complete
hash and Wine load logs. The virtual display failed OpenGL initialization even
with a software-rendering request, so effects/object runtime loads and gameplay
timing remain unverified. Next independent work: implement and differentially
test resource-name normalization for M2; pursue a working reference graphics
context separately. Candidate-source provenance remains unresolved; none is
compiled into the project. No recovered C++ game function is verified yet.
