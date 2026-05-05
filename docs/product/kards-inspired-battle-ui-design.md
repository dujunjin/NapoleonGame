# KARDS-Inspired Battle UI Design

Date: 2026-05-05
Status: Review draft
Prepared from: `ux-designer`, `ui-programmer`, and `gameplay-programmer` agent reviews
Primary audience: product review first, implementation agent second

## 1. Purpose

This document defines a KARDS-inspired battle UI direction for NapoleonGame.

The intent is not to copy KARDS. The useful reference points are:

- a readable battlefield with protected rear/support zones and a contested forward zone,
- visible HQ pressure,
- clear battle history,
- resource tension between deployment, movement, attacks, and orders,
- compact but information-rich card battlefield views.

This design covers two scopes:

1. **Current scope**: improve the existing HTML replay viewer in `prototypes/card-battle-sim/viewer.html`.
2. **Future scope**: define interaction principles for a later playable client.

The current implementation task should focus on the replay viewer. The future client section is guidance, not a requirement for the first implementation pass.

## 2. Design Goals

- Make the three-line battlefield readable at a glance: rear, main, skirmish/frontline, HQ.
- Help a reviewer understand causality: what changed, who caused it, and why it mattered.
- Keep the simulator useful for balance review: deterministic seeds, fast stepping, visible logs, and visible resource state.
- Preserve Napoleonic identity through terminology and presentation.
- Establish future playable-client principles without choosing an engine or final asset pipeline.

Success means a new viewer user can identify current turn, active side, current action, HQ health, orders, and changed units within 5 seconds.

## 3. Product Boundaries

### First Implementation Pass

Allowed:

- Edit `prototypes/card-battle-sim/viewer.html`.
- Keep the viewer as a single-file HTML/CSS/JS prototype.
- Use existing JSON data and snapshot diffs.
- Preserve existing match loading and preset dropdown behavior.
- Preserve attack arrows using existing `attack_event`.

Avoid:

- Rewriting simulator rules.
- Changing AI, combat, cards, balance, or victory settlement.
- Adding a frontend framework or build step.
- Requiring external art assets.
- Adding playable controls to the replay viewer.
- Making high-fidelity movement animation depend on fragile inference.

### Optional Later Export Pass

If the UI needs reliable animation or richer action presentation, extend `export_match.py` additively. Snapshots remain authoritative; metadata only improves presentation.

## 4. Information Architecture

### Primary Layer: Battlefield State

The board is the center of the experience:

- Enemy HQ and command state at the top.
- Enemy rear line.
- Enemy main line.
- Shared skirmish line as the contested forward zone.
- Player main line.
- Player rear line.
- Player HQ and command state at the bottom.

Each slot should have stable position, owner, unit type, attack, current/max HP, cost, and key status.

### Secondary Layer: Command State

Always visible:

- current turn,
- active side,
- current action type,
- step index and total steps,
- orders/军令,
- hand count,
- deck count,
- discard count,
- HQ HP.

### Tertiary Layer: Explanation

Used for review and debugging:

- current action summary,
- battle history,
- raw simulator log,
- keyword/event explanations where available,
- final result and end reason.

## 5. Replay Viewer UX

### 5.1 Page Layout

Use four zones:

1. **Replay Header**
   - Matchup, seed, winner/end reason when known.
   - Current turn, active player, step count.

2. **Battle Board**
   - Opponent command strip.
   - Five battlefield lines.
   - Player command strip.
   - SVG overlay for attack arrows and impact markers.

3. **Current Action Panel**
   - One concise summary of the selected timeline step.
   - Example: `第 5 回合 · 法兰西 · 攻击 · 近卫掷弹兵 → 普鲁士线列步兵 · 造成 3 伤害`.

4. **Battle History Panel**
   - Structured list of replay steps.
   - Preserve access to raw log lines for debugging.

The board should dominate the page. Logs explain the board; they should not carry the whole experience.

### 5.2 Replay Controls

Required controls:

- first step,
- previous action,
- play/pause,
- next action,
- final step,
- match selector.

Recommended controls:

- previous turn,
- next turn,
- speed selector: `0.5x / 1x / 2x / 4x`,
- step slider with action markers if feasible.

Keyboard:

- Left: previous action.
- Right: next action.
- Space: play/pause.
- Home: first step.
- End: final step.

Autoplay stops at the final step. Switching matches stops autoplay and resets to step 0.

### 5.3 Battlefield Lines

Keep the current five-line model:

- enemy rear,
- enemy main,
- skirmish line,
- player main,
- player rear.

The skirmish line should be the visual focus. It represents frontline pressure but does not need to copy KARDS' single-controller frontline rule.

Skirmish state labels:

- empty: `未接敌`,
- only player units: `我方压制`,
- only enemy units: `敌方压制`,
- both sides: `交战`.

Do not rely only on upside-down enemy cards. Add clear ownership labels or side markers, especially in the shared skirmish line.

### 5.4 Unit Battlefield Cards

Cards on the battlefield should use a compact battlefield view, not full printable card layout.

Required fields:

- cost,
- name,
- type,
- up to three keyword chips,
- attack,
- current/max HP.

State treatments:

- current step source: warm/gold or red-orange outline,
- current step target: bracket or impact outline,
- damaged HP: red number plus damage marker,
- destroyed this step: death marker or strong fade before disappearance when derivable,
- newly appeared unit: deploy pulse,
- changed unit: short highlight.

Do not fake unavailable state. If `can_act`, `has_acted_this_turn`, or `deployed_this_turn` is not exported, do not present it as certain.

### 5.5 Action Summary

Every step should have one readable action summary.

Prefer explicit metadata if available. For the first pass, derive from:

- `timeline[].action`,
- `timeline[].active_name`,
- first useful log line,
- `attack_event` for attacks,
- adjacent snapshot diff for HP/resource changes.

Avoid brittle deep parsing of Chinese log text. Simple category detection is acceptable.

### 5.6 Action Visualization

Action categories:

- deploy: destination slot pulse,
- advance: source/destination highlight if derivable,
- attack: arrow, attacker glow, target glow, damage badge,
- HQ attack: HQ impact state stronger than normal unit damage,
- event/order: command/effect flash on affected unit/line/HQ if derivable,
- start/end: no board effect required, but action panel should explain state.

For unsupported or ambiguous steps, fall back to:

- active player highlight,
- current action summary,
- history row.

### 5.7 Battle History

Replace the raw monospaced log as the primary history view with structured rows:

- turn,
- player/faction,
- action category,
- short description,
- damage/death/HQ marker when available.

Rows should be clickable and jump to the corresponding step. The current row should be highlighted.

Raw logs may remain in a secondary/debug area.

Optional filters:

- deploy,
- advance,
- attack,
- event,
- death,
- HQ.

### 5.8 Loading, Error, and Final States

Loading:

- show selected filename and loading state.

Error:

- do not show a blank board,
- mention likely local JSON/CORS issue,
- show the command:
  `cd prototypes/card-battle-sim && python3 -m http.server 8000`.

Final:

- final board remains visible,
- result panel shows winner, final turn, end reason, HQ totals, seed, factions,
- next/final controls are disabled or visibly inactive.

## 6. Data Support

### 6.1 Current JSON Supports

The current export can support a basic KARDS-inspired replay:

- matchup, seed, winner, final turn, end reason,
- per-action timeline stepping,
- active player,
- action category,
- full post-action board state,
- HQ HP,
- orders string,
- hand/deck/discard sizes,
- unit name/type/attack/current HP/max HP/cost/slot/keywords,
- existing `attack_event` for arrows and damage labels.

This is enough for the first viewer pass.

### 6.2 Snapshot Diff Can Derive

Adjacent snapshots can derive:

- HQ HP changes,
- hand/deck/discard count changes,
- orders changes,
- newly appeared units,
- removed units,
- HP deltas,
- attack/max HP changes,
- possible movement from one line/slot to another.

Caveat: without stable unit IDs, duplicate cards can make movement/death inference ambiguous. Ambiguous diffs should produce conservative highlights, not confident animation.

### 6.3 Recommended Additive Metadata

Later, add metadata without breaking old JSON:

- `schema_version`,
- `step_id`,
- numeric `current_orders` and `max_orders`,
- unit `id`,
- unit `card_id`,
- unit `owner`,
- unit `line`,
- `summary`,
- `action_detail`,
- `effects[]`.

Rules:

- Keep `meta` and `timeline` structure.
- Keep `timeline[].state` authoritative.
- Keep existing `action` strings.
- Keep existing `attack_event` fields and only add fields.
- Missing `schema_version` means current v1 behavior.
- New viewer should prefer metadata and fall back to snapshot diff.
- Old JSON must still load.

## 7. Future Playable Client Principles

This section is not part of the first replay viewer implementation.

### 7.1 Board Mental Model

- Player is always bottom.
- Opponent is always top.
- Rear line is deployment/support.
- Main line is combat staging.
- Skirmish line is the contested forward zone.

### 7.2 Core Actions

- Play unit/event from hand.
- Deploy unit to a legal slot.
- Advance unit toward the skirmish line.
- Select attacker, then select legal target.
- Play event/order with previewed targets and effects.
- End turn after pending effects resolve.

### 7.3 Input Model

Support both direct manipulation and accessible alternatives:

- Mouse/touch drag for spatial actions.
- Click/tap select then click/tap target.
- Keyboard focus, confirm, cancel, and legal-action navigation.
- Gamepad lane/slot navigation and contextual action button.

Drag is a convenience layer. Click/tap must be first-class.

### 7.4 Feedback Rules

Before committing:

- show legal targets,
- show cost,
- preview resource change,
- explain blocked actions.

On commit:

- animate movement/attack/effect,
- update numbers,
- append history.

Illegal action messages should be short and local:

- `军令不足`,
- `该线已满`,
- `本回合不能行动`,
- `目标超出射程`,
- `目标不合法`.

### 7.5 Progressive Disclosure

Default battlefield cards show essentials. Hover/focus/tap detail views can expand:

- keywords,
- aura effects,
- weather,
- commander effects,
- combat math.

## 8. Accessibility Requirements

- Replay controls must be usable with keyboard.
- Future play must support keyboard-only interaction.
- Do not encode faction, unit type, damage, or legality by color alone.
- Pair color with labels, icons, outlines, patterns, or position.
- Avoid relying on inverted enemy cards as the only ownership cue.
- Use visible focus states for buttons, cards, slots, timeline controls, and history rows.
- Add `aria-label` for icon-only controls.
- Add `aria-live="polite"` for current action summary.
- Respect `prefers-reduced-motion` for autoplay transitions, attack arrows, shake, and damage effects.
- Text must not overflow inside buttons, cards, or status strips at desktop or narrow mobile widths.

## 9. Visual Direction

The visual direction is a Napoleonic staff-table interface:

- campaign map surface,
- paper cards,
- faction-colored frames,
- brass/gold command highlights,
- red impact/damage,
- blue-gray weather/effect states,
- green recovery/buff states,
- restrained military report typography.

Avoid a one-note brown/tan palette. The current prototype is already very brown; the next pass should add faction color, slate ink, command gold, muted map green, and red damage contrast.

## 10. Acceptance Criteria

### Replay Viewer

The implementation is acceptable when:

- The viewer loads existing match JSON files.
- Match switching still works.
- Step forward/back, start, final, and autoplay still work.
- Keyboard stepping and play/pause work.
- Current turn, active side, step count, seed, factions, and result/end reason are visible.
- The five battlefield lines are clear and stable.
- The skirmish line communicates empty, friendly pressure, enemy pressure, or contested state.
- Current action is visible in a summary panel.
- Attack steps show attacker, target, arrow, and damage/HQ impact when data allows.
- Changed units or HQ values are highlighted when derivable.
- Battle history is structured by step and current step is highlighted.
- Clicking a history row jumps to that step.
- Raw log remains accessible for debugging.
- Layout is usable around 1280px desktop width.
- Layout remains functional around 390px mobile width.
- No replay-only UI implies that the user can take playable actions.

### Future Playable Client

A future playable implementation should be judged by:

- every legal action has visible affordance before confirmation,
- rejected actions explain why,
- drag and click/tap paths are both supported,
- resource cost is visible before committing,
- latest opponent action is understandable without raw log reading,
- combat resolution remains legible with or without animations,
- event/weather/commander effects have distinct feedback.

## 11. Product Owner Decisions

These decisions should be reviewed before implementation expands beyond the first viewer pass:

- Keep three distinct lines long-term, or move toward a simpler support/frontline model?
- Is the skirmish line permanently shared/contested, or only a prototype representation?
- Should future playable deployment be drag-first, click-first, or equal support for both?
- Should replay/spectator mode reveal hidden information such as hand contents, deck order, or AI reasoning?
- Should playtest UI remain primarily Chinese, or become bilingual?
- Should the next viewer pass prioritize debugging clarity or cinematic presentation?

Recommended defaults for first pass:

- keep the existing three-line model,
- treat the skirmish line as shared/contested,
- keep UI primarily Chinese,
- prioritize debugging clarity over cinematic presentation,
- do not reveal hidden hand contents because current export only has hand size.

## 12. Handoff To Implementation Agent

Assign the first implementation to `ui-programmer`.

Implementation prompt:

```text
Read docs/product/kards-inspired-battle-ui-design.md and implement only the Replay Viewer scope.

Edit only prototypes/card-battle-sim/viewer.html unless you explicitly ask for approval.
Do not change rules, balance, AI, cards, tests, or match data semantics.
Keep the viewer single-file and framework-free.
Preserve current match loading, preset dropdown, attack arrows, and playback controls.
Use current JSON plus conservative snapshot diff.
If a requested visual requires stable unit IDs or richer action metadata, leave a clear fallback and report the metadata gap instead of changing gameplay.
```

