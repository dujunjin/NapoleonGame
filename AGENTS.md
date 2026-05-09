# NapoleonGame — Project Memory

## Project Overview

Napoleonic card tactics game. Engine-independent Python rules simulator with KARDS-inspired HTML replay viewer, printable card PDF, and historical research documents.

- **Engine**: TBD (engine decision deferred until human playtest)
- **Language**: Python (prototypes); target engine language TBD
- **Template**: Based on Claude Code Game Studios

## Current State (2026-05-08)

**Simulator**: `prototypes/card-battle-sim/`
- 3 factions: France, Prussia, Russia — 33 cards each
- HQ 14 HP, full-round victory settlement
- v0.2 mechanics: Operational Pressure (turn 18+), Breakthrough Reward
- v0.3A: Command Layer (1 commander per faction, 1 tactical objective per player)
- v0.3B: trigger system, sub-faction tags, 12-card richness expansion
- Per-action timeline with attack arrow visualization
- 86 unit tests passing

**Balance baseline** (`python3 ecosystem_test.py 500 0`):
- 法兰西: 46.2% / 普鲁士: 51.7% / 俄罗斯: 52.1%
- PacingRisk: 0.169 (target <=0.30) ✅
- Mirror first-player rates <=65% ✅
- Shaken frequency: ~6.2 applications/match (target 1-6)

**Viewer**: Epic Napoleonic replay viewer (`viewer.html`):
- Grid layout: title banner, battle board (75%), timeline sidebar (25%)
- Fixed bottom playback bar with progress scrubber and speed toggle
- Timeline sidebar with turn-grouped event cards (replaces history table)
- HQ health bars with critical pulse, attack arrows with flow animation
- Screen shake on attacks, floating damage numbers, deploy/attack/death animations
- 5 battlefield lines with skirmish state labels
- Keyboard controls, responsive, `prefers-reduced-motion` support
- Design spec: `docs/product/kards-inspired-battle-ui-design.md`
- Redesign plan: `design/ux/battle-replay-viewer-redesign-plan.md`

**Known issues**:
- France win rate (46.2%) slightly below 47% — acceptable for prototype phase

## Key Files

| File | Purpose |
|---|---|
| `cards.py` | Faction decks, card definitions, keywords |
| `game.py` | Turn loop, deploy, advance, event resolution |
| `ai.py` | AI decision: deploy, advance, attack targeting |
| `combat.py` | Damage calc, attack targets, range |
| `game_state.py` | Player, Battlefield, BattleUnit dataclasses |
| `export_match.py` | Per-action timeline JSON export |
| `viewer.html` | KARDS-inspired HTML replay viewer |
| `ecosystem_test.py` | Deterministic 3-faction balance test |
| `test_rule_tuning.py` | Main Python unittest suite |
| `generate_pdf.py` | Printable card PDF (platform-aware font) |
| `generate_pdf.py` | Printable card PDF (platform-aware font) |

## Recent Changes

- v0.4 Shaken morale marker: `is_shaken` on BattleUnit, trigger at ≤ half HP after ≥2 damage, -1 attack, cannot advance, recovery at owner turn end
- F2 fix: event-card `advance_friendly_one_no_attack` now excludes Shaken units
- Balance post-Shaken: 法兰西 46.2%, 普鲁士 51.7%, 俄罗斯 52.1%, PacingRisk 0.169
- KARDS-inspired viewer rewrite: 4-zone layout, structured history, action summary, responsive
- Event card package: commander + weather events for all 3 factions
- Attack arrow visualization: SVG arrows from attacker to defender
- Per-action sub-steps: timeline broken into deploy/advance/attack actions
- v0.3B trigger/sub-faction richness: deploy/advance/attack/wounded/destroy/sequence/same-line hooks
- Balance pass: France nerfed, Russia buff (焦土政策 HQ 2→1)
- Full-round victory settlement (both players act, then check HQ)
- Deterministic ecosystem test seeds
- PDF font path platform-aware (macOS/Linux/Windows)

## Useful Commands

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py          # Run main rule tests
python3 -m unittest test_viewer_export_contract.py # Run viewer/export contract tests
python3 ecosystem_test.py 500 0                  # Balance test (deterministic)
python3 export_match.py FRANCE RUSSIA 42         # Export match replay
python3 generate_pdf.py                          # Generate printable PDF
python3 -m http.server 8080                      # Serve viewer at localhost:8080
```

## Hierarchical Agent Map

This repository uses local `AGENTS.md` files to keep context close to the files being edited.

| Path | Role | Use When |
|---|---|---|
| `design/AGENTS.md` | Design documents, research, entity registry | Editing GDDs, research summaries, entity naming, or design requirements |
| `docs/AGENTS.md` | Architecture/product/process documentation | Editing ADRs, product specs, workflow docs, plans, or technical references |
| `prototypes/AGENTS.md` | Prototype family overview | Choosing between current simulator, visual prototype, and legacy simulator |
| `prototypes/card-battle-sim/AGENTS.md` | Current active rules simulator | Editing gameplay rules, cards, AI, balance, exports, viewer, or printable PDF |
| `prototypes/card-battle-visual-prototype/AGENTS.md` | Standalone visual/interaction prototype | Editing React/Babel visual exploration files only |
| `prototypes/rule-simulator/AGENTS.md` | Legacy command-line simulator | Reading historical design experiments; avoid treating it as current gameplay source |

Current approved next implementation plan: `.sisyphus/plans/napoleon-light-morale-cohesion.md`.

Do not create new engine-specific source under `src/` until the engine decision brief is revisited after human playtest.


<claude-mem-context>
# Memory Context

# [NapoleonGame] recent context, 2026-05-08 4:25am GMT+8

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 1 obs (102t read) | 4,776t work | 98% savings

### May 5, 2026
**403** 1:50a 🟣 **claude-hud statusline setup requested**
The user requested claude-hud:setup to configure their Claude Code statusline. No tool executions or configuration changes were observed during this session to record durable outcomes.

S213 Debug claude-hud statusLine setup — after run.sh fixes didn't resolve the issue, now testing whether statusLine itself works with a minimal echo command (May 5 at 2:10 AM)
S216 Debug claude-hud statusLine — root cause found: project-level `.claude/settings.json` was overriding user-level config (May 5 at 2:12 AM)
S217 Continue executing Napoleon Game development - visual polish completion and KARDS-like interaction plan creation (May 5 at 2:19 AM)
### May 8, 2026
S218 Test connection to Claude Code session (May 8 at 3:58 AM)
**Investigated**: Nothing investigated — the session received only a "test" message with no tool executions or substantive work.

**Learned**: The connection is working; the assistant responded confirming readiness.

**Completed**: No work was completed. The session remains at its starting state.

**Next Steps**: Awaiting an actual task or request from the user to begin work.


Access 5k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>
