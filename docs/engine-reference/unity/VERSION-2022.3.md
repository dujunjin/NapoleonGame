# Unity 2022.3 — Project Version Reference

| Field | Value |
|---|---|
| Engine Version | 2022.3.62f3c1 |
| Project Pinned | 2026-07-16 |
| Local Editor Verified | Yes, macOS Unity Hub install |
| Knowledge Risk | LOW — stable LTS API surface |
| Upgrade Candidate | Unity 6.3 LTS |

## Project Rules

- Use runtime UI Toolkit APIs available in 2022.3; do not copy Unity 6-only examples.
- Use pure C# for authoritative rules and NUnit/EditMode tests.
- Use direct serialized asset references for this small vertical slice; do not add Addressables speculatively.
- An upgrade must pass the gate in `docs/engine-decision-brief.md`.

## Verified References

- https://docs.unity3d.com/2022.3/Documentation/Manual/UIElements.html
- https://docs.unity3d.com/2022.3/Documentation/Manual/testing-editortestsrunner.html

