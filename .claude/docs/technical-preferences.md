# Technical Preferences

<!-- Populated by /setup-engine. Updated as the user makes decisions throughout development. -->
<!-- All agents reference this file for project-specific standards and conventions. -->

## Engine & Language

- **Engine**: TBD — engine decision intentionally deferred.
- **Language**: Python for current prototypes; target engine language TBD.
- **Rendering**: HTML/CSS for current viewer; target engine renderer TBD.
- **Physics**: None in current card prototype.

## Input & Platform

<!-- Written by /setup-engine. Read by /ux-design, /ux-review, /test-setup, /team-ui, and /dev-story -->
<!-- to scope interaction specs, test helpers, and implementation to the correct input methods. -->

- **Target Platforms**: PC/Web for prototype evaluation; final targets TBD.
- **Input Methods**: Keyboard/Mouse for current viewer; paper prototype for human playtests.
- **Primary Input**: Mouse.
- **Gamepad Support**: None for current prototype.
- **Touch Support**: None for current prototype.
- **Platform Notes**: Card text and board state must remain readable at desktop browser sizes before engine selection.

## Naming Conventions

- **Classes**: PascalCase for Python classes; follow target engine convention after setup.
- **Variables**: snake_case in Python prototypes.
- **Signals/Events**: Not configured until engine selection.
- **Files**: snake_case Python files; descriptive kebab-case or snake_case docs.
- **Scenes/Prefabs**: Not configured until engine selection.
- **Constants**: UPPER_SNAKE_CASE in Python prototypes.

## Performance Budgets

- **Target Framerate**: Not applicable to Python simulator; viewer should remain responsive in a desktop browser.
- **Frame Budget**: TBD after engine selection.
- **Draw Calls**: TBD after engine selection.
- **Memory Ceiling**: TBD after engine selection.

## Testing

- **Framework**: Python `unittest` for current simulator.
- **Minimum Coverage**: Focused regression tests for rule changes; broad coverage after architecture phase.
- **Required Tests**: Balance formulas, gameplay systems, replay export integrity.

## Forbidden Patterns

<!-- Add patterns that should never appear in this project's codebase -->
- [None configured yet — add as architectural decisions are made]

## Allowed Libraries / Addons

<!-- Add approved third-party dependencies here -->
- [None configured yet — add as dependencies are approved]

## Architecture Decisions Log

<!-- Quick reference linking to full ADRs in docs/architecture/ -->
- [No ADRs yet — use /architecture-decision to create one]

## Engine Specialists

<!-- Written by /setup-engine when engine is configured. -->
<!-- Read by /code-review, /architecture-decision, /architecture-review, and team skills -->
<!-- to know which specialist to spawn for engine-specific validation. -->

- **Primary**: TBD until engine selection.
- **Language/Code Specialist**: Python/general gameplay review for current prototype; target-engine specialist after `/setup-engine`.
- **Shader Specialist**: None for current prototype.
- **UI Specialist**: General UI/UX review for current HTML viewer; target-engine UI specialist after `/setup-engine`.
- **Additional Specialists**: game-designer, systems-designer, economy-designer, qa-lead, prototyper.
- **Routing Notes**: Use engine-neutral agents for prototype work. Use Godot/Unity/Unreal specialists only after the engine decision is made.

### File Extension Routing

<!-- Skills use this table to select the right specialist per file type. -->
<!-- Engine-specific routing should be filled after /setup-engine. -->

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (primary language) | General gameplay review for Python prototypes |
| Shader / material files | None until engine selection |
| UI / screen files | General UI/UX review for HTML viewer |
| Scene / prefab / level files | None until engine selection |
| Native extension / plugin files | None until engine selection |
| General architecture review | technical-director |
