# NapoleonGame Unity Vertical Slice

Unity 2022.3.62f3c1 desktop player-versus-AI demo. The client uses a pure C# rules assembly and UI Toolkit presentation.

## Generate card data

From the repository root:

```bash
python3 tools/export_unity_card_catalog.py
```

## Open

Open `src/NapoleonGame.Unity` in Unity Hub with editor `2022.3.62f3c1`. The generated scene is `Assets/NapoleonGame/Scenes/Battle.unity`.

## Controls

- Click a card or friendly unit to reveal legal targets, then click a target.
- Drag cards and units toward a labelled target. Targets magnetize within a 44 px tolerance; invalid drops rebound.
- `D`: deploy the first legal unit; `M`: make the first legal advance; `A`: make the first legal attack.
- `Space` or `E`: end turn; `N`: new match; `Escape`: cancel the current selection.
- Use the reduced-motion toggle to remove non-essential motion.

The current macOS build is written to `output/unity/NapoleonLinesOfCommand.app`.

## Batch verification

```bash
/Applications/Unity/Hub/Editor/2022.3.62f3c1/Unity.app/Contents/MacOS/Unity \
  -batchmode -quit -projectPath "$PWD/src/NapoleonGame.Unity" \
  -runTests -testPlatform EditMode -testResults "$PWD/output/unity/editmode-results.xml"
```
