# Technical Preferences

<!-- Populated by /setup-engine. Updated as the user makes decisions throughout development. -->
<!-- All agents reference this file for project-specific standards and conventions. -->

## Engine & Language

- **Engine**: Unity 2022.3.62f3c1.
- **Language**: C# for the Unity client; Python for prototype regression and balance.
- **Rendering**: UI Toolkit screen-space 2D/2.5D presentation.
- **Physics**: None in current card prototype.

## Input & Platform

<!-- Written by /setup-engine. Read by /ux-design, /ux-review, /test-setup, /team-ui, and /dev-story -->
<!-- to scope interaction specs, test helpers, and implementation to the correct input methods. -->

- **Target Platforms**: macOS development build and Windows/macOS desktop demo.
- **Input Methods**: Mouse and keyboard.
- **Primary Input**: Mouse.
- **Gamepad Support**: Deferred; all commands remain dispatchable so it can be added later.
- **Touch Support**: None for current prototype.
- **Platform Notes**: Design for 16:9 at 1920x1080 and remain usable at 1280x720. Essential rules cannot depend on hover alone.

## Naming Conventions

- **Classes**: PascalCase; one public C# type per matching file.
- **Variables**: `_camelCase` private fields, PascalCase public properties, camelCase locals.
- **Signals/Events**: immutable domain events and explicit command dispatch; UI never owns rules state.
- **Files**: PascalCase C# files; descriptive kebab-case docs.
- **Scenes/Prefabs**: PascalCase; the vertical slice uses one generated `BattleDemo` scene.
- **Constants**: PascalCase in C#, UPPER_SNAKE_CASE in Python.

## Performance Budgets

- **Target Framerate**: 60 fps on an integrated-GPU development Mac.
- **Frame Budget**: 16.6 ms total; UI scripts <= 2 ms during steady state.
- **Draw Calls**: <= 80 for the battle screen after warm-up.
- **Memory Ceiling**: <= 512 MB for the desktop demo after one full match.

## Testing

- **Framework**: Unity Test Framework/NUnit for C#; Python `unittest` for the simulator.
- **Minimum Coverage**: Focused regression tests for rule changes; broad coverage after architecture phase.
- **Required Tests**: deterministic setup, resource economy, frontline control, legal targets, combat, victory, AI completion, card catalog, and Python regression.

## Forbidden Patterns

<!-- Add patterns that should never appear in this project's codebase -->
- Rules in `MonoBehaviour`, `VisualElement`, animation callbacks, or scene objects.
- UI code directly mutating HP, credits, zones, cards, or turn state.
- `Resources.Load`, `FindObjectOfType`, `SendMessage`, legacy `Input.*`, or per-frame LINQ.
- Randomness not supplied by the seeded match RNG.

## Allowed Libraries / Addons

<!-- Add approved third-party dependencies here -->
- Unity built-in UI Toolkit.
- Unity Test Framework supplied by the editor.
- No third-party runtime packages in the first vertical slice.

## Architecture Decisions Log

<!-- Quick reference linking to full ADRs in docs/architecture/ -->
- `docs/architecture/adr-0001-unity-client-architecture.md`

## Engine Specialists

<!-- Written by /setup-engine when engine is configured. -->
<!-- Read by /code-review, /architecture-decision, /architecture-review, and team skills -->
<!-- to know which specialist to spawn for engine-specific validation. -->

- **Primary**: unity-specialist.
- **Language/Code Specialist**: unity-specialist for C# architecture and review.
- **Shader Specialist**: unity-shader-specialist if custom shaders are introduced later.
- **UI Specialist**: unity-ui-specialist for UXML, USS, pointer input, and accessibility.
- **Additional Specialists**: gameplay-programmer, game-designer, systems-designer, qa-lead.
- **Routing Notes**: Keep rules engine pure C#; route UI and scene work separately from domain logic.

### File Extension Routing

<!-- Skills use this table to select the right specialist per file type. -->
<!-- Engine-specific routing should be filled after /setup-engine. -->

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (`.cs`) | unity-specialist |
| Shader / material files | unity-shader-specialist |
| UI (`.uxml`, `.uss`) | unity-ui-specialist |
| Scene / prefab files | unity-specialist |
| Native extension / plugin files | unity-specialist |
| General architecture review | unity-specialist + technical-director |
