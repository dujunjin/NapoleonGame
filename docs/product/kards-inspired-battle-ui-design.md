# KARDS-Inspired Battle UI Product Design

Date: 2026-05-05
Status: Review draft
Audience: product review, implementation model, later acceptance review
Scope: current HTML replay viewer plus future playable client interaction model

## 1. Purpose

This document defines a KARDS-inspired battle UI direction for NapoleonGame.

The goal is not to copy KARDS visually or mechanically. The goal is to borrow the parts that are useful for a Napoleonic card tactics game:

- A tactical tabletop battlefield with clear lines of contact.
- A strong distinction between deployed reserves, engaged troops, and contested forward positions.
- Shared action resources that make deployment, movement, and attacks compete for attention.
- Immediate, readable feedback for what happened in each action.
- A UI that can start as an HTML replay viewer and later become the basis for a playable client.

The design has two layers:

1. **Replay Viewer Layer**: improve `prototypes/card-battle-sim/viewer.html` so AI matches are easier to read, review, and use for balance/design discussions.
2. **Playable Client Layer**: define the interaction principles and state model that a future engine implementation should follow.

## 2. Product Goals

### 2.1 Primary Goals

- Make a battle state understandable within 3 seconds: who is winning, who is active, where the pressure is, and what just happened.
- Make the three-line battlefield feel like the core tactical identity of the game.
- Make each action in a replay readable without reading raw logs first.
- Make unit affordances clear: can act, cannot act, damaged, newly deployed, target, attacker, destroyed.
- Preserve the historical tabletop mood: campaign map, staff table, paper cards, line formations, military reports.

### 2.2 Secondary Goals

- Prepare UI language for future human play without forcing the current viewer to become interactive.
- Make the design usable by another model as an implementation brief.
- Keep the first implementation small enough to finish inside the current HTML prototype.

## 3. Non-Goals

- Do not redesign game rules in this document.
- Do not replace the Python simulator.
- Do not introduce account systems, deck building UI, shop UI, progression UI, or matchmaking.
- Do not require a game engine decision.
- Do not require final art assets.
- Do not implement drag-and-drop in the replay viewer.
- Do not add new balance mechanics just to support UI.

## 4. Design Principles

### 4.1 Tactical Lines First

The battlefield should read from top to bottom as a tactical situation, not as a generic card grid.

Use the existing NapoleonGame lines:

- Enemy Rear
- Enemy Main
- Skirmish Line
- Player Main
- Player Rear

The Skirmish Line is the visual equivalent of a contested frontline. It should be visually stronger than the other lines and should communicate control, pressure, and exposure.

### 4.2 Action Replay Before Log Reading

The user should understand a step from the board itself:

- Which unit acted.
- What kind of action happened.
- Which target was affected.
- How values changed.
- Whether a unit died.

The text log supports the board; it should not be the only way to understand the action.

### 4.3 Resources Are Operational Pressure

The current game uses `orders` as the action resource. The UI should present this as operational command capacity, not only as a number.

Use the Chinese label **军令** in the current viewer. In future client UI, treat it as the single budget for:

- deploying cards,
- advancing units,
- attacking,
- playing events/orders.

### 4.4 Visual State Beats Explanatory Text

Prefer icons, color, borders, badges, and line highlights over long instructional text.

Allowed explanatory text:

- Short log entries.
- Tooltips or detail panels.
- Empty/error states.
- Design-time labels for the replay viewer.

Avoid visible in-app paragraphs explaining how to use the UI.

### 4.5 Viewer Is a Review Tool

The current viewer exists to help designers inspect AI matches. It should optimize for:

- scrubbing through actions,
- comparing before/after states,
- spotting pacing problems,
- seeing repeated tactical patterns,
- sharing match seeds and outcomes.

It does not need to optimize for player onboarding yet.

## 5. Current State Summary

The existing `viewer.html` already provides:

- match data loading from JSON,
- step forward/back and autoplay,
- player info bars,
- five battlefield rows,
- unit cards with cost, name, type, keywords, attack, and HP,
- attack arrows,
- text log panel,
- match preset selector.

The exported JSON already provides:

- match metadata,
- per-action timeline,
- active player,
- action name,
- log lines,
- serialized battlefield state.

The next UI pass should improve information hierarchy and state feedback without demanding a full data rewrite.

## 6. Replay Viewer Design

### 6.1 Page Structure

The replay viewer should use a three-zone structure:

1. **Command Bar**
   - Match identity, result, seed, turn, active player, step counter.
   - Playback controls.
   - Match selector.

2. **Battle Table**
   - Player status strip for enemy.
   - Enemy Rear.
   - Enemy Main.
   - Skirmish Line.
   - Player Main.
   - Player Rear.
   - Player status strip for player.
   - SVG/action overlay for arrows and impact effects.

3. **After-Action Panel**
   - Current action summary.
   - Battle history list.
   - Optional selected unit detail if a unit is clicked.

The battle table should remain the visual center of the page. Logs and metadata should support it, not compete with it.

### 6.2 Command Bar

The command bar should show:

- `法兰西 vs 俄罗斯`
- seed
- final result when known
- current turn
- active player/faction
- step number, for example `42 / 118`
- playback controls

Controls:

- Start
- Previous action
- Play/Pause
- Next action
- Final
- Match selector

Keyboard behavior:

- Left arrow: previous action
- Right arrow: next action
- Space: play/pause
- Home: first step
- End: final step

The existing emoji-style button labels may stay for the prototype, but the layout should not depend on emoji width.

### 6.3 Player Status Strips

Each player status strip should show:

- faction and player label,
- HQ HP,
- current/max 军令,
- hand size,
- deck size,
- discard size.

State emphasis:

- Active player strip receives a gold border or glow.
- HQ HP below 50% receives warning color.
- HQ HP below 25% receives danger color.
- Changed values in the current step flash briefly or show a small delta badge.

For replay review, the status strip should be compact. Avoid large cards for player info.

### 6.4 Battlefield Lines

Each line should have:

- a stable line label,
- four fixed slots,
- empty slot placeholders,
- line-level highlight when involved in the current action.

Line mood:

- Rear lines: guarded, muted, reserve-like.
- Main lines: standard formation line.
- Skirmish Line: contested, brighter, dashed or map-marker treatment.

The Skirmish Line should show control or pressure:

- If only P1 has units in the Skirmish Line, mark as `我方压制`.
- If only P2 has units in the Skirmish Line, mark as `敌方压制`.
- If both have units, mark as `交战`.
- If empty, mark as `未接敌`.

If the rules currently allow both players in Skirmish Line, represent it as contested occupancy. Do not force KARDS' single-controller frontline rule into the current game.

### 6.5 Unit Card Battlefield View

Battlefield units should use a reduced card view, not full printable card art.

Required fields:

- action/operation cost or deployment cost as currently available,
- name,
- unit type,
- up to three keyword badges/icons,
- attack,
- current/max HP.

Recommended state treatments:

- Can act: warm/gold action rim.
- Cannot act: neutral rim.
- Newly deployed this turn: small `新` badge.
- Has acted this turn: dimmed action marker.
- Damaged: HP in red.
- Buffed attack or HP if exported later: green number.
- Destroyed in current step: collapse/fade treatment or grave marker before removal, if previous-step diff can identify it.
- Current attacker: red/orange outline.
- Current target: white or red targeting bracket.
- Affected by event/weather: blue/gray effect badge.

For the first implementation, if exported data does not include `can_act`, `has_acted_this_turn`, or `deployed_this_turn`, do not fake these states. Add only states that can be derived from current and previous snapshots.

### 6.6 Action Overlay

Each timeline step should produce one concise board-level visual event.

Action types:

- Deploy: card/slot pulse on the destination line.
- Advance: movement arrow from previous line/slot to new line/slot.
- Attack: arrow from attacker to target plus damage badge.
- Event/order: command seal or effect flash over affected units/line/HQ.
- Cleanup/death: red damage flash and destroyed marker.
- Start/end: no action overlay, only history summary.

Attack arrows already exist and should be retained. They should be visually strong for the current step but not obscure card stats.

For ambiguous or unsupported action types, fall back to:

- highlight active player,
- show current action summary,
- append clear history entry.

### 6.7 Current Action Summary

Add a compact summary immediately below or beside the battle table.

It should show:

- action category,
- actor,
- target if any,
- numerical result if any,
- log line.

Example:

`攻击 · 法兰西线列步兵 -> 俄国猎兵 · 造成 2 伤害`

If the exported step only has raw log lines, the first log line may be used as the summary. Implementation should avoid brittle text parsing beyond simple category detection.

### 6.8 Battle History

The battle history should become a structured list instead of a raw monospaced block.

Each row:

- turn number,
- player/faction,
- action icon/category,
- short description,
- optional damage/death marker.

History rows should be clickable:

- Clicking a row jumps to that timeline step.
- Current step row is highlighted.

History should auto-scroll to the current step during autoplay but not fight the user if they manually scroll. A simple first implementation may always keep current row visible.

### 6.9 Unit Detail Panel

Clicking a unit should open or update a small detail panel in the After-Action Panel.

Show:

- name,
- faction if known,
- type,
- attack,
- HP,
- cost,
- keywords,
- current line and slot.

This is useful for review because battlefield cards are intentionally compact.

If no unit is selected, the panel shows current action summary.

### 6.10 Responsive Behavior

Desktop target:

- Battle table and after-action panel can be side-by-side on wide screens.
- On medium screens, after-action panel sits below battle table.

Mobile target:

- Viewer remains usable, not perfect.
- Command bar wraps into two rows.
- Battlefield remains horizontally constrained with smaller fixed cards.
- History appears below the board.
- No text should overflow inside buttons, cards, or status strips.

The viewer does not need a mobile-first redesign in the first pass, but it must not break layout.

## 7. Future Playable Client Design

### 7.1 Interaction Model

The playable client should support both drag and click interactions.

Desktop:

- Drag a card from hand to a legal line/slot to deploy.
- Click a unit to show available actions.
- Drag a unit to a legal line/slot to advance.
- Drag or click an attacker, then click a valid target to attack.
- Click an event/order card, then click target if required.

Touch/mobile:

- Tap card/unit to select.
- Legal targets/slots are highlighted.
- Tap target/slot to confirm.
- Tap outside or cancel button to cancel.

The click/tap model is mandatory for accessibility and mobile. Drag is a convenience layer, not the only interaction.

### 7.2 Selection State

The client should use a clear selection state machine:

1. Idle
2. Card selected from hand
3. Unit selected on board
4. Targeting
5. Confirming or resolving
6. Animation lock
7. Return to Idle

At any selected state:

- legal destinations are highlighted,
- illegal destinations are not highlighted,
- a cancel affordance exists,
- the selected object is visually anchored.

### 7.3 Legal Action Feedback

Legal actions:

- slots glow gold,
- targets receive brackets,
- affected lines receive subtle highlight,
- command cost is shown before confirmation.

Illegal actions:

- do not require trial-and-error,
- show a short reason when attempted,
- examples: `军令不足`, `该线已满`, `本回合不能行动`, `目标超出射程`, `必须先进入散兵线`.

The error message should appear near the attempted object and fade. Avoid modal dialogs for normal illegal actions.

### 7.4 Resource UI

The resource display should answer:

- How much command capacity do I have now?
- What will this action cost?
- Will I have enough after this?

When selecting an action:

- show current/max 军令,
- preview cost subtraction,
- use warning color if the action consumes the remaining resource.

Future implementation may represent 军令 as pips/tokens plus number. The current viewer can remain number-based.

### 7.5 Hand UI

Playable hand should show:

- cards fanned or laid in a stable row,
- affordable cards highlighted,
- unaffordable cards muted,
- cards with conditional restrictions visibly locked or neutral,
- hover/tap detail expansion.

Cards should not jump or resize unpredictably when hovered. Use stable dimensions and overlays.

### 7.6 Targeting and Combat

When a unit is selected to attack:

- valid targets are bracketed,
- invalid units remain visible but muted,
- HQ targeting is clearly distinct from unit targeting,
- expected damage can be previewed if the simulator can provide it.

When combat resolves:

- attacker pulse,
- projectile/charge line,
- target impact,
- HP change,
- death removal,
- history row appended.

The action should remain understandable even if animations are disabled or skipped.

### 7.7 Events, Commanders, and Weather

Events should use a command-card interaction:

- select event from hand,
- show target requirements,
- highlight affected line/unit/HQ,
- resolve with a distinct command seal/effect treatment.

Weather should be represented as a board-level state:

- visible weather banner or token,
- duration if applicable,
- affected lines or actions indicated with small icons.

Commander events should feel like command decisions, not normal unit deployment:

- use a different action category in history,
- show command portrait/seal if art exists later,
- apply board highlights to affected units.

### 7.8 Battle History in Play

Playable history should include:

- latest opponent action,
- expandable full history,
- filters are not required for first playable version.

The latest opponent action should remain visible long enough for the player to understand what changed before taking their own turn.

### 7.9 End Turn and Turn Start

The End Turn button should be prominent only for the active player.

At turn start:

- draw/resource changes should be shown in sequence,
- refreshed units should regain action indicators,
- current weather/event effects should pulse if they matter.

The player should never need to infer that a new turn started only from log text.

## 8. Data and Implementation Notes

### 8.1 Existing Data Can Support First Pass

The viewer can implement most review improvements using:

- current step,
- previous step,
- action string,
- log lines,
- unit `name`,
- unit `slot`,
- unit `type`,
- unit `attack`,
- unit `current_hp`,
- unit `max_hp`,
- unit `cost`,
- unit `keywords`,
- HQ HP and player stats.

The implementation model should prefer snapshot diffs over log parsing where possible.

Examples:

- HP delta: compare previous and current HP for matching unit identity.
- New unit: exists in current step but not previous step at same player/line/slot/name.
- Removed unit: exists in previous step but not current.
- HQ damage: compare previous/current HQ HP.

### 8.2 Recommended Future Export Fields

Later, `export_match.py` should add explicit action metadata:

```json
{
  "action": "attack",
  "actor": {
    "player": 0,
    "line": "main",
    "slot": 1,
    "name": "..."
  },
  "target": {
    "player": 1,
    "line": "rear",
    "slot": 1,
    "name": "..."
  },
  "result": {
    "damage": 2,
    "destroyed": false,
    "hq_delta": 0
  }
}
```

Do not block the viewer redesign on this. Use it as a future enhancement.

## 9. Visual Direction

### 9.1 Mood

Use a Napoleonic staff-table direction:

- campaign map surface,
- muted paper and leather,
- faction accents,
- brass/gold command highlights,
- red impact/damage,
- blue/gray weather/effect,
- green recovery/buff.

Avoid a UI dominated by one brown or tan palette. The current prototype is very brown; the next pass should add contrast through faction color, brass, red damage, muted map green, and slate ink.

### 9.2 Typography

Use readable Chinese UI typography. Keep:

- compact labels,
- short action summaries,
- stable card names,
- no decorative letter spacing that hurts readability.

Large title typography should be reserved for the page header. Compact panels should use smaller, tighter headings.

### 9.3 Icons

The current HTML can use text badges first. A later pass can replace them with icons.

Suggested categories:

- deploy,
- advance,
- attack,
- event,
- weather,
- death,
- HQ damage,
- resource change.

Icons should always have a tooltip or accessible label.

## 10. Acceptance Criteria

### 10.1 Replay Viewer Acceptance

The implementation is acceptable when:

- A reviewer can identify current turn, active player, current step, and match result from the command bar.
- The five battlefield lines are clearly labeled and visually distinct.
- The Skirmish Line communicates empty, friendly pressure, enemy pressure, or contested state.
- Current action is visible as both a board highlight/overlay and a short text summary.
- Attack actions show attacker, target, and damage/HQ change when data allows.
- Deploy and movement-like actions show at least destination highlight.
- Battle history is structured by step and clicking a history row jumps to that step.
- Unit click opens a detail panel or equivalent detail view.
- Previous/next/play/final/start controls still work.
- Keyboard controls still work or are added if missing.
- Layout does not overflow on a typical desktop width around 1280px.
- Layout remains usable at a narrow/mobile width around 390px, even if less polished.
- Existing match JSON files still load.

### 10.2 Future Playable Client Acceptance

A future playable implementation should be judged against these principles:

- Every legal action has a visible affordance before confirmation.
- Every rejected action gives a short reason.
- Drag and click/tap interaction paths are both supported.
- Resource cost is visible before committing an action.
- The latest opponent action is understandable without reading a raw log.
- Combat resolution remains legible with or without animations.
- Weather/event/commander effects have distinct board-level feedback.

## 11. Implementation Boundaries for Another Model

For the first implementation model, assign only the replay viewer layer unless explicitly expanding scope.

Allowed:

- Edit `prototypes/card-battle-sim/viewer.html`.
- Add CSS/JS inside the same file if staying with the current single-file prototype.
- Optionally update `export_match.py` only for additive metadata that does not break existing JSON.
- Keep all existing match controls functional.

Avoid:

- Rewriting simulator rules.
- Replacing the viewer with a framework.
- Adding build tooling.
- Requiring external assets.
- Changing balance, AI, card definitions, or tests unless needed for additive export metadata.

## 12. Review Checklist

Use this checklist during product review:

- Does the design still feel Napoleonic rather than WWII reskinned?
- Is the Skirmish Line the center of tactical attention?
- Can a designer review an AI match faster than before?
- Are logs supporting the board instead of carrying the whole experience?
- Are future playable interactions defined without overbuilding the current viewer?
- Is there any requirement here that forces an engine decision? If yes, remove it.

