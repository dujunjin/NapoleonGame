# ADR-0001: Unity Client with Pure C# Authoritative Domain

## Status

Accepted

## Date

2026-07-16

## Last Verified

2026-07-16

## Decision Makers

Project owner and Codex implementation agent.

## Summary

Build the playable desktop vertical slice in Unity 2022.3.62f3c1. Keep authoritative rules in a pure C# assembly, drive UI and animations from commands/events, and preserve the Python simulator as a migration oracle.

## Engine Compatibility

| Field | Value |
|---|---|
| Engine | Unity 2022.3.62f3c1 |
| Domain | Core, UI, Input, Animation |
| Knowledge Risk | LOW |
| References Consulted | `docs/engine-reference/unity/VERSION-2022.3.md`, official UI Toolkit docs |
| Post-Cutoff APIs Used | None |
| Verification Required | Batch EditMode/PlayMode tests and macOS development build |

## ADR Dependencies

| Field | Value |
|---|---|
| Depends On | None |
| Enables | Unity gameplay/UI implementation |
| Blocks | None after acceptance |
| Ordering Note | Domain contracts and tests precede presentation code |

## Context

### Problem Statement

The project has a tested Python rules prototype and browser visuals but no engine client. Directly porting rules into scene scripts would make balance regression, deterministic tests, and future networking difficult.

### Current State

The Python simulator owns gameplay truth; HTML/React prototypes duplicate portions of rules and presentation. Unity is installed locally but no Unity project exists.

### Constraints

- Preserve the dirty working tree and existing prototypes.
- Deliver a desktop player-versus-AI demo before online or mobile work.
- Support deterministic headless tests.
- Keep the vertical slice dependency-light and buildable with the installed editor.

### Requirements

- Rules must run without scenes, GameObjects, or frame timing.
- UI sends validated commands and renders snapshots/events.
- Animation failure cannot corrupt match state.
- Three 33-card faction catalogs load from one generated source.
- Steady-state UI scripting stays within 2 ms at 60 fps on the development Mac.

## Decision

Create `src/NapoleonGame.Unity/` with four assembly boundaries: Domain, Application/AI, Runtime Presentation, and Tests. The domain exposes commands, results, immutable-style snapshots, and ordered game events. Runtime UI Toolkit code binds those outputs to the battle screen and serializes animation playback.

### Architecture

```text
Python cards.py -> catalog exporter -> card_catalog.json
                                      |
                                      v
UI Toolkit -> PlayerCommand -> MatchController -> Pure C# GameEngine
    ^                                  |                 |
    |                                  v                 v
    +------ ViewSnapshot <------ AnimationQueue <--- GameEvent[]
                                      |
                               Seeded AI commands
```

### Key Interfaces

```csharp
public interface IGameEngine {
    CommandResult Execute(GameCommand command);
    GameSnapshot Snapshot();
    IReadOnlyList<GameAction> GetLegalActions(int playerId);
}

public interface IAgent {
    GameCommand Choose(GameSnapshot snapshot, IReadOnlyList<GameAction> legalActions);
}
```

### Implementation Guidelines

- No Unity references in Domain.
- One seeded RNG belongs to the match; random APIs are injected or wrapped.
- UI callbacks dispatch commands only; they do not edit domain objects.
- Domain events are facts, not animation instructions. Presentation maps facts to effects.
- Use UXML/USS for layout/theme and C# manipulators for drag input.
- Use serialized direct references for the small vertical slice; revisit Addressables only when content scale requires it.

## Alternatives Considered

### Alternative 1: MonoBehaviour-Centric Rules

- **Description**: Store cards, turns, and combat directly on scene components.
- **Pros**: Fast first screenshot.
- **Cons**: Frame-coupled logic, weak tests, fragile save/replay/network paths.
- **Estimated Effort**: Lower initially, higher after first feature wave.
- **Rejection Reason**: Conflicts with deterministic migration and verification goals.

### Alternative 2: Embed Python at Runtime

- **Description**: Keep Python authoritative and call it from Unity.
- **Pros**: Minimal rule rewrite.
- **Cons**: Packaging, platform, debugging, and performance complexity; poor Unity integration.
- **Estimated Effort**: Medium with high deployment risk.
- **Rejection Reason**: Unsuitable for a portable Unity client.

## Consequences

### Positive

- Fast deterministic tests, clean replay/save seam, and presentation-independent rules.
- Python remains useful for differential checks during migration.
- UI and animations can be replaced without rewriting combat.

### Negative

- More upfront types and mapping code.
- Temporary duplication exists until Unity parity is established.

### Neutral

- Unity 6.3 upgrade is deferred behind an explicit test/build gate.

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---:|---:|---|
| Rule drift between Python and C# | Medium | High | Contract tests and catalog generation |
| UI Toolkit 2022 animation limitations | Medium | Medium | Small C# animation queue and reduced-motion fallback |
| Scope growth into online CCG | High | High | Explicit vertical-slice exclusions |
| Generated art inconsistency | Medium | Low | Shared prompt/style guide and procedural fallbacks |

## Performance Implications

| Metric | Before | Expected After | Budget |
|---|---:|---:|---:|
| CPU frame time | Browser prototype only | <=16.6 ms | 16.6 ms |
| UI scripts | Unknown | <=2 ms steady state | 2 ms |
| Memory | Unknown | <=512 MB | 512 MB |
| Load time | N/A | <=5 s development build | 5 s |

## Migration Plan

1. Generate the Unity card catalog from Python and validate counts.
2. Implement/test C# economy, zones, combat, events, and AI.
3. Bind UI Toolkit presentation and event-driven animations.
4. Build and play a complete desktop match; retain Python until parity is accepted.

**Rollback plan**: Delete only `src/NapoleonGame.Unity/` and new Unity-specific docs; the Python/browser prototypes remain runnable.

## Validation Criteria

- [ ] Unity EditMode tests pass in batch mode.
- [ ] A development build completes with no compile errors.
- [ ] Any faction can finish an AI match from the battle UI.
- [ ] Same seed/commands produce the same snapshot hash.

## GDD Requirements Addressed

| GDD Document | System | Requirement | How This ADR Satisfies It |
|---|---|---|---|
| `design/gdd/kards-inspired-battle-system.md` | Battle | Deterministic playable player-vs-AI vertical slice | Pure C# engine plus seeded AI and tests |
| `design/gdd/kards-inspired-battle-system.md` | Presentation | Animation must not alter domain state | Command/event/snapshot separation |

## Related

- `docs/engine-decision-brief.md`
- `docs/product/card-game-ui-interaction-research-report.md`
- `src/NapoleonGame.Unity/`

