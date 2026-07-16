# Unity KARDS-Inspired Vertical Slice — Execution Plan

**Goal**: Deliver a desktop Unity demo where the player selects one of three Napoleonic factions and completes a match against deterministic AI using the new Support/Frontline rules.

## Work Sequence

1. Accept Unity and battle-system decisions; preserve Python as the migration oracle.
2. Create the Unity project, assemblies, test layout, generated scene, and build entry point.
3. Export all three 33-card catalogs and implement the pure C# match engine, legal actions, combat, events, AI, and snapshots.
4. Build the UI Toolkit battle screen with KARDS-like information hierarchy and direct manipulation.
5. Add original Napoleonic card/board art direction plus deploy, move, attack, damage, death, turn, and victory motion.
6. Run Python regression, Unity tests, catalog validation, and a macOS development build; capture evidence.

## Completion Gates

- 144 existing Python tests remain green.
- Unity EditMode and PlayMode tests pass in batch mode.
- Each faction loads 33 cards.
- A seeded AI match finishes without invalid state or deadlock.
- The battle screen works at 1920x1080 and 1280x720.
- Build output launches to a playable faction-select/battle flow.

## Deliberate Exclusions

- Online PvP, accounts, deck building, collection economy, packs, store, mobile build, localization beyond Chinese, and production live-ops.
- KARDS logos, card frames, art, text, audio, or proprietary presentation assets.
- Unity 6.3 migration before the vertical-slice test/build gate passes.
