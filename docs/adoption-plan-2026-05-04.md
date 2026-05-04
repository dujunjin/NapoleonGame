# Adoption Plan: Napoleon Card Game

**Date**: 2026-05-04  
**Source Template**: Claude Code Game Studios  
**Project State**: Existing rules prototype, viewer prototype, printable card prototype, and research docs  

## Summary

This project is being adopted into Claude Code Game Studios as a brownfield prototype. The goal is to gain the template's agent workflow, design gates, QA structure, and production tracking without prematurely choosing an engine or moving existing working files.

Current artifacts have been migrated into the Game Studios layout:

- `prototypes/rule-simulator/` -- earlier command-line rules simulator.
- `prototypes/card-battle-sim/` -- active simulator, AI replay viewer, JSON replay export, balance tests, and printable PDF.
- `design/research/napoleon/` -- historical and card-game research.

## Current Gaps

- [ ] Engine is intentionally not configured. Use `docs/engine-decision-brief.md` before `/setup-engine`.
- [x] Existing prototype files have been migrated under `prototypes/`.
- [ ] GDD coverage is minimal. `design/gdd/game-concept.md` and `systems-index.md` now provide the starting point.
- [ ] No ADRs exist yet. Engine choice, data model, replay format, and UI architecture should each become ADRs later.
- [ ] No formal playtest reports exist yet. Future paper or viewer playtests should be logged under `production/playtests/`.
- [ ] No sprint plan exists yet. Create one after engine direction and next prototype milestone are agreed.

## Migration Plan

1. [ ] Use the current viewer and PDF to run at least one human playtest.
   - Output: `production/playtests/playtest-YYYY-MM-DD.md`.
   - Estimate: 1 session.

2. [ ] Review `docs/engine-decision-brief.md`.
   - Decision: keep engine TBD, choose Godot, choose Unity, or create a separate tech spike.
   - Estimate: 30 minutes.

3. [ ] If an engine is chosen, run the template's `/setup-engine` workflow in Claude Code.
   - Output: configured `CLAUDE.md` and `.claude/docs/technical-preferences.md`.
   - Estimate: 30 minutes.

4. [x] Convert the active Python prototype into a documented prototype package.
   - Target: `prototypes/card-battle-sim/`.
   - Validation: run `python3 -m unittest test_rule_tuning.py` and `python3 export_match.py FRANCE RUSSIA 42` from the migrated directory.

5. [ ] Create ADRs after the next decision point.
   - `docs/architecture/adr-0001-engine-selection.md`
   - `docs/architecture/adr-0002-card-data-model.md`
   - `docs/architecture/adr-0003-replay-format.md`
   - Estimate: 1 session.

6. [ ] Create first production sprint after ADRs.
   - Likely sprint goal: "Human-playtestable card tactics prototype with clearer hand, aura, and death feedback."
   - Estimate: 30 minutes.

## Operating Rules During Adoption

- Existing prototypes are source-of-truth until engine production begins.
- Do not rewrite the simulator into an engine just to satisfy folder structure.
- Use Game Studios agents for review, planning, QA, balance, and engine decision support.
- Keep code changes small and verifiable with `test_rule_tuning.py`, `export_match.py`, and `ecosystem_test.py`.
