# Napoleon Card Game -- Claude Code Game Studios Configuration

Napoleonic card tactics game development managed through Claude Code Game Studios.
The project currently has an engine-independent Python rules simulator, HTML match
viewer, printable card PDF, and historical research documents.

## Technology Stack

- **Engine**: TBD. Do not lock the project to Godot, Unity, or Unreal until the engine decision brief is reviewed.
- **Language**: Python for current rules prototypes; target engine language TBD.
- **Version Control**: Git with trunk-based development
- **Build System**: Prototype scripts for now; engine build pipeline TBD.
- **Asset Pipeline**: Research docs, generated JSON replays, HTML viewer, and PDF card prototype for now.

> **Current rule**: Treat `prototypes/rule-simulator/` and
> `prototypes/card-battle-sim/` as engine-independent prototypes.
> Do not migrate or rewrite them into an engine until the GDD, playtest feedback,
> and engine decision brief are reviewed.

## Project Structure

@.claude/docs/directory-structure.md

## Current Project Artifacts

- `prototypes/rule-simulator/` -- earlier Python command-line simulator.
- `prototypes/card-battle-sim/` -- current Python simulator, HTML AI match viewer, JSON replays, tests, and printable PDF.
- `design/research/napoleon/` -- Napoleonic setting and card game research.
- `design/gdd/game-concept.md` -- project concept adapted for Game Studios.
- `docs/engine-decision-brief.md` -- engine selection deferred decision brief.
- `docs/adoption-plan-2026-05-04.md` -- brownfield adoption plan for this repo.

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
