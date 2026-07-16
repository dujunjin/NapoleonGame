# Engine Decision Brief

**Status**: Accepted  
**Last Updated**: 2026-07-16  

## Decision

Use **Unity 2022.3.62f3c1 with C#** for the first playable desktop vertical slice. This is the verified local LTS editor, so the project can be created, tested, and built immediately. Re-evaluate an upgrade to Unity 6.3 LTS only after the vertical slice is stable and covered by Unity tests.

The Unity client lives under `src/NapoleonGame.Unity/`. The existing Python simulator remains a regression and balance oracle during migration; it is not deleted or silently rewritten.

## Why Decide Now

The original deferral trigger has been met: the next milestone explicitly requires Unity-specific runtime UI, direct manipulation, animation, assets, and desktop builds. The existing simulator is healthy (144 tests passing on 2026-07-16), so it can anchor a controlled migration.

- Does the three-line battlefield create readable decisions?
- Does the draw/order economy stay interesting after turn 8?
- Are faction identities understandable?
- Do players understand deaths, aura effects, HQ pressure, and artillery constraints?

The selected milestone is a single-player desktop demo, not a production online CCG. Networking, account systems, monetization, and live content delivery remain out of scope.

## Current Candidates

| Engine | Fit | Strengths | Risks |
|---|---|---|---|
| Godot 4 | Strong for 2D PC/Web card prototype | Fast iteration, open source, simple UI and 2D workflow, low overhead | Smaller commercial ecosystem, console path less direct |
| Unity | Strong if mobile/long-term commercial pipeline matters | Mature C#, asset store, mobile and console ecosystem, UI tooling options | Heavier editor, licensing trust concerns, more setup overhead |
| Unreal Engine 5 | Weak for current scope | High-end 3D and cinematic presentation | Overkill for a card tactics prototype unless 3D spectacle becomes central |

## Selected Technical Direction

- Runtime UI: UI Toolkit (UXML/USS) for the board, cards, HUD, history, and menus.
- Rules: pure C# domain assembly with no `MonoBehaviour` dependency.
- Presentation: event-driven animation queue; UI never mutates authoritative state directly.
- Data: generated JSON catalog sourced from the Python card definitions, converted to domain objects at startup.
- Target: 16:9 desktop, mouse-first; keyboard cancel/end-turn shortcuts; no hover-only essential information.
- Rendering: UI-focused 2D/2.5D presentation; no DOTS, custom render pipeline, networking, or Addressables in the first vertical slice.

## Decision Triggers

Revisit this decision when one of these happens:

- A human playtest confirms the card rules are worth turning into a digital vertical slice.
- The target platform is chosen.
- The intended presentation is chosen: pure 2D card table, 2.5D board, or 3D battlefield.
- The next milestone requires engine-specific UI, animation, asset, or deployment work.

## Upgrade Gate

Upgrade from Unity 2022.3.62f3c1 to Unity 6.3 LTS only when all of the following hold:

1. EditMode and PlayMode tests pass in the current editor.
2. A desktop build completes and a full AI match is playable.
3. The project has no dependency on APIs removed or changed in Unity 6.
4. The upgrade is performed on a dedicated branch with before/after screenshots and test results.
