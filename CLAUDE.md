# Napoleon Card Game -- Claude Code Game Studios Configuration

Napoleonic card tactics game development managed through Claude Code Game Studios.
The project has an engine-independent Python rules simulator and a Unity playable
vertical slice, plus a KARDS-inspired HTML replay viewer and research documents.

## Technology Stack

- **Engine**: Unity 2022.3.62f3c1 (first playable vertical slice)
- **Language**: C# for Unity; Python remains the prototype/balance oracle.
- **Version Control**: Git with trunk-based development
- **Build System**: Unity Build Pipeline plus Python prototype verification.
- **Asset Pipeline**: Unity Asset Import Pipeline; generated card catalog; direct serialized references for the vertical slice.

> **Current rule**: Treat `prototypes/card-battle-sim/` as a read-only behavioral
> oracle while the new rules are migrated deliberately into
> `src/NapoleonGame.Unity/`. Do not delete it or claim parity without differential
> tests. New production gameplay code belongs in the Unity project.

## Project Structure

@.claude/docs/directory-structure.md

## Current Project Artifacts

- `prototypes/rule-simulator/` -- earlier Python command-line simulator.
- `prototypes/card-battle-sim/` -- current Python simulator, KARDS-inspired HTML replay viewer, JSON replays (per-action sub-steps), tests, and printable PDF.
- `design/research/napoleon/` -- Napoleonic setting and card game research.
- `design/gdd/game-concept.md` -- project concept adapted for Game Studios.
- `docs/product/kards-inspired-battle-ui-design.md` -- KARDS-inspired replay viewer design spec.
- `docs/engine-decision-brief.md` -- engine selection deferred decision brief.
- `docs/adoption-plan-2026-05-04.md` -- brownfield adoption plan for this repo.
- `docs/superpowers/specs/2026-05-07-v03b-card-richness-design.md` -- v0.3B card-effect richness design spec (triggers, sub-faction tags, 12 new cards).
- `prototypes/card-battle-sim/triggers.py` -- v0.3B trigger dispatch module (MAX_CHAIN_DEPTH, trigger evaluation, sub-faction bonuses).
- `prototypes/card-battle-visual-prototype/` -- React + Babel standalone visual prototype for interaction feel exploration.
- `docs/superpowers/specs/2026-05-08-v04-visual-polish-design.md` -- v0.4 interaction polish design spec (drag, attack, shake, banner).
- `docs/superpowers/plans/2026-05-08-v04-visual-polish-implementation.md` -- v0.4 implementation plan (9 tasks, 6 phases).

## Current Game State

**Simulator**: 3 factions (France, Prussia, Russia), 33 cards each, HQ 14 HP.
- Commander + weather event cards (France 2, Prussia 5, Russia 3)
- v0.3B trigger system: 7 trigger types (On Deploy, On Advance, On Attack, On Wounded, On Destroy, Same-line Threshold, Sequence)
- v0.3B sub-faction tags: Imperial Guard (France), Landwehr (Prussia), Cossack (Russia)
- 12 new cards (4 per faction) with trigger effects
- PlayLog for Sequence trigger evaluation
- Full-round victory settlement (both players act, then check HQ)
- Per-action timeline export with attack arrow visualization
- Deterministic ecosystem test seeds

**Balance baseline** (`python3 ecosystem_test.py 200 0`):
- 法兰西: 49.6% / 普鲁士: 50.5% / 俄罗斯: 49.9%
- PacingRisk: 0.147 (target ≤ 0.30)
- Mirror first-player rates ≤ 65%

**Tests**: `python3 -m unittest test_rule_tuning.py` (86 tests)

**Viewer**: KARDS-inspired replay viewer (`viewer.html`):
- Four-zone layout: header, battle board, action panel, history panel
- 5 battlefield lines with skirmish state labels
- Structured history rows (clickable), collapsible raw log
- Speed selector (0.5x-4x), keyboard controls (Left/Right/Space/Home/End)
- Responsive: desktop 1280px, mobile 390px
- Design spec: `docs/product/kards-inspired-battle-ui-design.md`

**Visual Prototype** (`prototypes/card-battle-visual-prototype/`):
- React 18 + Babel standalone, no build step. Run: `python3 -m http.server 8010`
- v0.4 interaction polish (9 tasks complete):
  - CSS token system (4 easing curves, 8 duration tokens)
  - Pointer events + rAF drag (8px threshold, bounce-back, ESC cancel)
  - Hand fan: dynamic angle, hover zoom 1.45×, large card preview
  - Attack drag-arrow (Hearthstone-style, replaces click model)
  - Staged attack choreography (wind-up → lunge → freeze → recoil → counter)
  - Shake scaling by damage (Vlambeer rule: shake only on damage taken)
  - Skippable banner (600ms), AI spinner, 800ms AI delay
  - Action queue (length-1 FIFO, accepts input during animations)
- 3 matchups (法/普, 法/俄, 普/俄), 4 Tweak controls, 3 card styles
- Smoke test: `prototypes/card-battle-visual-prototype/manual-smoke-2026-05-08.md`

## Engine Version Reference

@docs/engine-decision-brief.md

## Technical Preferences

@.claude/docs/technical-preferences.md

## Coordination Rules

@.claude/docs/coordination-rules.md

## Collaboration Protocol

**User-driven collaboration, not autonomous execution.**
Every task follows: **Question -> Options -> Decision -> Draft -> Approval**

- Agents MUST ask "May I write this to [filepath]?" before using Write/Edit tools
- Agents MUST show drafts or summaries before requesting approval
- Multi-file changes require explicit approval for the full changeset
- No commits without user instruction

See `docs/COLLABORATIVE-DESIGN-PRINCIPLE.md` for full protocol and examples.

> **First session?** If the project has no engine configured and no game concept,
> run `/start` to begin the guided onboarding flow.

## Coding Standards

@.claude/docs/coding-standards.md

## Context Management

@.claude/docs/context-management.md
