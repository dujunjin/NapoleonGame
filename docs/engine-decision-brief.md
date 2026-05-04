# Engine Decision Brief

**Status**: Deferred  
**Last Updated**: 2026-05-04  

## Decision

Do not choose a production engine yet. The project should remain engine-independent until at least one human playtest validates the core rules and interaction model.

## Why Defer

The strongest current assets are the Python simulator, AI replay viewer, and printable card prototype. These answer design questions faster than an engine build:

- Does the three-line battlefield create readable decisions?
- Does the draw/order economy stay interesting after turn 8?
- Are faction identities understandable?
- Do players understand deaths, aura effects, HQ pressure, and artillery constraints?

An engine decision before these answers risks optimizing the wrong implementation.

## Current Candidates

| Engine | Fit | Strengths | Risks |
|---|---|---|---|
| Godot 4 | Strong for 2D PC/Web card prototype | Fast iteration, open source, simple UI and 2D workflow, low overhead | Smaller commercial ecosystem, console path less direct |
| Unity | Strong if mobile/long-term commercial pipeline matters | Mature C#, asset store, mobile and console ecosystem, UI tooling options | Heavier editor, licensing trust concerns, more setup overhead |
| Unreal Engine 5 | Weak for current scope | High-end 3D and cinematic presentation | Overkill for a card tactics prototype unless 3D spectacle becomes central |

## Current Recommendation

Default recommendation is **Godot 4** if the next milestone is a 2D digital card prototype for PC/Web.

Choose **Unity** instead if the next milestone explicitly targets mobile, larger asset-store leverage, or a team already comfortable with C#.

Avoid **Unreal** unless the product direction changes toward a 3D cinematic battlefield where visual fidelity is a core pillar.

## Decision Triggers

Revisit this decision when one of these happens:

- A human playtest confirms the card rules are worth turning into a digital vertical slice.
- The target platform is chosen.
- The intended presentation is chosen: pure 2D card table, 2.5D board, or 3D battlefield.
- The next milestone requires engine-specific UI, animation, asset, or deployment work.

## Next Step

After the next playtest, either:

1. Run `/setup-engine godot` if the goal is a focused 2D PC/Web vertical slice.
2. Run `/setup-engine unity` if mobile or Unity ecosystem support becomes important.
3. Keep engine TBD and continue paper/browser prototype iteration if rules are still unstable.
