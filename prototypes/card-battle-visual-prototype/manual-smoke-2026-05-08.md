# Manual Smoke Test — v0.4 Visual Polish
Date: 2026-05-08
Tester: _____

## Instructions
Open `http://localhost:8010/` (run `python3 -m http.server 8010` from the prototype directory).
Test each criterion below. Fill in Pass/Fail and Notes.

| # | Criterion | Pass/Fail | Notes |
|---|-----------|-----------|-------|
| 1 | Drag does not cause visible stutter (smooth 60fps) | | |
| 2 | Drag below 8px = click, card stays in hand | | |
| 3 | Invalid drop bounces card back (~250ms) | | |
| 4 | Pressing ESC during drag returns card to hand | | |
| 5 | Hovering one hand card does not move sibling cards | | |
| 6 | Hover preview large card visible at top-right | | |
| 7 | During drag: valid slots glow gold, invalid slots dimmed | | |
| 8 | Attack via drag arrow works (press P1 unit → drag → release on enemy) | | |
| 9 | Long-distance lunge visibly slower than short-distance | | |
| 10 | Freeze frame at impact is observable (~90ms pause) | | |
| 11 | Counter damage arrives after initial impact, not simultaneously | | |
| 12 | 1-HP kill produces subtle shake; 4-HP kill produces strong shake | | |
| 13 | Deploying a card produces no shake | | |
| 14 | Damage numbers overshoot (bounce past target size) | | |
| 15 | Click during animation → action queues and executes after | | |
| 16 | Banner is skippable (click during banner) | | |
| 17 | P2 HQ shows spinner during AI turn | | |
| 18 | All 3 matchups work (法/普, 法/俄, 普/俄) | | |
| 19 | All 4 Tweak controls work (bgKind, mood, cardStyle, speed) | | |

## Results Summary
- Total: ___/19
- Pass: ___
- Fail: ___
