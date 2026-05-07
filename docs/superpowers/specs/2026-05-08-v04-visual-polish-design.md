# v0.4 Visual Prototype · Interaction Polish Design

**Date:** 2026-05-08
**Status:** Draft
**Scope:** `prototypes/card-battle-visual-prototype/` only (does not touch `card-battle-sim/`)
**Codename:** "Silky" (丝滑化)

---

## 1. Goal And Scope

Make the React visual prototype feel "丝滑" — fluid, responsive, and physically credible — by closing the largest interaction-feel gaps identified in the diagnosis, without introducing audio asset dependencies or migrating to real replay data.

**In scope:**
- Easing/timing token system (4 curves, 8 durations)
- Drag-to-deploy rewrite (rAF + transform direct, threshold, bounce-back, ESC cancel)
- Hand-fan polish (dynamic angle, hover-zoom without re-fan, large preview)
- Drop-zone telegraph (dim invalid, glow valid)
- Attack declare via drag-arrow (Hearthstone-style)
- Attack choreography (wind-up → distance-aware lunge → freeze frame → staged counter)
- Damage shake scaling + Vlambeer-rule (taken-only)
- Damage number overshoot
- Action queue (length 1, accept input during animation)
- Skippable turn banner + AI-thinking spinner

**Out of scope:**
- Audio (deferred to v0.5)
- Mobile / touch (drag refactored to use pointer events as a dependency, but no explicit mobile testing)
- Connecting to `card-battle-sim/match_data.json` (independent work item)
- Keyboard accessibility / screen reader support (independent work item)
- Production-quality React migration (still a prototype)

---

## 2. Pain Points Addressed

From the 2026-05-08 diagnosis pass on `battlefield.jsx`:

1. **Drag re-render storm** — `dragPos` is `useState`, mutated every `mousemove`, causing one React commit per pixel.
2. **No drag threshold** — pressing on a card immediately enters drag, eating clicks.
3. **No bounce-back** — invalid drops just dismiss; cards vanish from the cursor.
4. **Attack timing collapse** — fixed 280ms hit + 100ms counter = three combat moments overlap.
5. **Hand fan rigid** — angle `i*6°` independent of hand size; hover only translates, no large-card preview.
6. **Blocked turn flow** — 1500ms AI delay with no telegraph, banner unskippable.
7. **No input queueing** — clicks during animations are dropped.
8. **Uniform shake** — every event shakes equally; desensitizes the eye.

---

## 3. Design Pillars

**P1 · 4 curves cover everything.** All animations choose from 4 named easings, exposed as CSS variables. New random `cubic-bezier` values are not allowed.

**P2 · Input first.** Animations never drop user input. The most recent input during a lock is queued and executed when the lock releases.

**P3 · Causal feedback.** Shake, flash, and damage numbers scale with the magnitude of damage taken. Routine actions (deploy, advance) cause no shake.

**P4 · No information blockers.** No banner runs ≥800ms without a skip. AI thinking is always visible.

---

## 4. Easing And Duration Tokens

New file: `prototypes/card-battle-visual-prototype/tokens.css`. Loaded by `index.html` before the JSX bundles.

```css
:root {
  /* 4 curves */
  --ease-snap-in:    cubic-bezier(0.20, 0.90, 0.30, 1.00);  /* snappy enter */
  --ease-rest:       cubic-bezier(0.00, 0.00, 0.20, 1.00);  /* decelerate to rest */
  --ease-overshoot:  cubic-bezier(0.34, 1.56, 0.64, 1.00);  /* anticipate-overshoot */
  --ease-hover:      ease-in-out;                            /* symmetric hover */

  /* Durations */
  --dur-snap:        240ms;
  --dur-rest:        280ms;
  --dur-overshoot:   380ms;
  --dur-hover:       150ms;

  /* Interaction tunables */
  --drag-threshold:  8px;
  --bounce-back:     250ms;
  --ai-pause:        800ms;
  --banner-hold:     600ms;

  /* Shake (px = base + dmg * per_dmg, capped) */
  --shake-base:      4;
  --shake-per-dmg:   1.5;
  --shake-cap:       12;
}
```

JSX reads via `getComputedStyle(document.documentElement).getPropertyValue('--dur-snap')` only where values must be numeric (e.g., `setTimeout`); otherwise CSS uses them directly.

---

## 5. Component Changes

### 5.1 Drag System Rewrite (`battlefield.jsx:550–597`)

**Before:** `useState` on `dragPos`, written on every `mousemove`, one React commit per pixel.

**After:**
- `dragRef = useRef({ x: 0, y: 0, active: false, startX, startY })`
- `pointerdown` records start, sets `active: false` (not yet lifted), captures the pointer with `setPointerCapture`
- `pointermove` writes `transform: translate(...)` directly to the ghost element via DOM ref, batched in a single `requestAnimationFrame`. No `setState`.
- Drag does not lift until `Math.hypot(dx, dy) > 8px`. Below threshold = click (no-op currently).
- `hoveredSlotRef` toggles a CSS class on the slot element directly; no state write.
- ESC key listener cancels drag → bounce-back.
- Invalid release: animate ghost back to the card's hand position over 250ms `var(--ease-rest)` with scale 1.1 → 1.0, then dispose.

The migration from `mousedown/mousemove/mouseup` to pointer events is mandatory; it is the foundation that makes future touch support a configuration change rather than a rewrite.

**Acceptance:** DevTools "Performance" recording during a 1-second drag shows ≤2 React commits (start, end). No `dragPos` state in the React tree.

### 5.2 Hand Fan (`battlefield.jsx:954–985`)

- Angle: `(i - (N - 1)/2) * Math.min(8, 70 / N)` — caps total fan span at 70° regardless of hand size.
- Hover: only the hovered card transforms (scale 1.45×, lift 78px, rotate 0°). Sibling cards do **not** re-fan.
- Hover preview: a fixed-position large card (scale 2.2×) renders in the top-right corner of the stage, anchored at `right: 220, top: 80`, fade in 150ms `var(--ease-hover)`. Disappears on hover-out.

**Acceptance:** Hovering one card in a 7-card hand does not visually move any sibling card.

### 5.3 Drop-Zone Telegraph (`Slot`, `Line` in `battlefield.jsx`)

During drag (`draggingCard != null`):
- Valid slots (empty + line is in `canP1Deploy`'s allowed set for the card): outer border 2px gold (`f1.gold`), inner glow `box-shadow: inset 0 0 12px rgba(212,165,92,0.4)`.
- Invalid slots: opacity 0.4 (this is the telegraph that matters more than the highlight per Sakamoto, GDC 2015).
- Hovered slot (under cursor): brighter gold border + scale 1.04.

Cost-too-high pickup: morale UI (P1 morale bar) flashes red 1× over 200ms.

**Acceptance:** Mid-drag, every empty slot on a non-deployable line shows visibly dimmer than every empty slot on a deployable line.

### 5.4 Attack Declare via Drag-Arrow (replaces click-target in `battlefield.jsx:641–700`)

**Before:** `handleUnitClick` sets `selectedAttacker`, second click on enemy unit calls `attackTarget`.

**After:**
- `pointerdown` on a P1 unit that has not advanced this turn: enter "targeting" mode, store `{ line, idx, originX, originY }`.
- `pointermove`: render an SVG quadratic Bézier arrow from origin to cursor, with a subtle fletching cap. Curve control point pulled 30px upward to give arc.
- `pointerup` on enemy unit slot: call `attackTarget(line, idx, targetLine, targetIdx)`.
- `pointerup` on `[data-hq="p2"]`: call `attackTarget(line, idx, null, null)` (HQ attack).
- `pointerup` on empty space, ESC, or right-click: cancel; arrow fades 150ms.

The previous click-attacker → click-target model is removed. Selection is implicit during the drag.

**Acceptance:** Pressing on a P1 unit with mouse and dragging onto an enemy unit then releasing produces the attack. No click-then-click sequence is required.

### 5.5 Attack Choreography (`attackTarget`, `battlefield.jsx:702–773`)

Replace fixed-280ms with a 4-stage timeline (all `setTimeout`s gated by the action queue lock from §5.8):

| Stage | Time (ms) | Effect |
|---|---|---|
| 0 — wind-up | t=0..80 | Attacker scales 0.95× and rotates 5° away from target. `var(--ease-snap-in)`. |
| 1 — lunge | t=80..80+L | Attacker translates `dist * 0.55` toward target. `L = min(380, 240 + dist/3)`, `var(--ease-overshoot)`. |
| 2 — freeze frame | t=80+L..170+L | All visible motion paused 90ms. Spawn impact particles (flash + 12 sparks + 6 staggered smokes). Damage number spawns now. |
| 3 — recoil | t=170+L..170+L+220 | Attacker returns to origin. `var(--ease-rest)`. |
| 4 — counter | t=390+L | If target survived, spawn counter damage on attacker (was t=380 in old code with no relation to lunge length). |
| 5 — death | t=590+L | If target/attacker died, animate fade + remove. |

**Acceptance:** A long-distance attack visibly takes longer than a short-distance attack. The freeze frame is observable (a single video frame ~16ms is too short; 90ms is intentional).

### 5.6 Damage Shake Scaling (`shake` flag, full-stage transform)

Replace boolean `shake` with `shakeAmp: number`. Compute when applying damage:

```js
const amp = Math.min(SHAKE_CAP, SHAKE_BASE + dmg * SHAKE_PER_DMG);
```

Shake fires **only when the player on this side takes damage** (Vlambeer rule). Routine deploy / advance never shakes. Apply via stage CSS keyframes parameterized by `--shake-amp`. Decay 200ms.

**Acceptance:** Killing a 1-HP target produces ~5.5px shake; killing a 4-HP target produces ~10px shake; deploying a card produces 0 shake.

### 5.7 Damage Numbers (`spawnParticle('damage', ...)`)

Change CSS animation from current `damage-pop` to use `var(--ease-overshoot)` for the initial pop (0–30%), then float upward 50px over 700ms total, fade in last 300ms.

**Acceptance:** Damage number visibly bounces past target size before settling.

### 5.8 Action Queue (`useActionQueue` hook, new module)

New hook in `battlefield.jsx` (or extracted to `action-queue.jsx`):

```js
function useActionQueue() {
  const [locked, setLocked] = useState(false);
  const pendingRef = useRef(null);

  const tryRun = useCallback((fn) => {
    if (locked) {
      pendingRef.current = fn;  // capacity = 1 (overwrite)
      return false;
    }
    setLocked(true);
    fn(() => {
      setLocked(false);
      const next = pendingRef.current;
      pendingRef.current = null;
      if (next) tryRun(next);
    });
    return true;
  }, [locked]);

  return { locked, tryRun, queued: !!pendingRef.current };
}
```

`deployCard` and `attackTarget` are wrapped: each accepts a `done` callback and calls it when its full timeline completes.

UI: a small "queued" indicator (subtle gold pulse) appears next to the cursor when an action is queued.

**Capacity = 1.** Multiple queued clicks overwrite the pending action — prevents runaway and respects "most recent input wins".

**Acceptance:** Click attack mid-deploy-animation; deploy completes, then attack starts. Click twice mid-animation; only the second click's action runs after the lock releases.

### 5.9 Turn Banner + AI Spinner (`TurnBanner`, `endTurn`)

- Banner duration: 600ms (was implicit ~1500ms).
- Banner accepts click or any keypress to skip; on skip, transitions immediately to next phase.
- AI spinner: a small rotating laurel icon appears next to P2's avatar within 200ms of `endTurn()` and disappears when AI deploy completes. Implemented as a CSS `animation: rotate 1s linear infinite`.
- AI deploy delay: 800ms (was 1500ms).

**Acceptance:** Pressing space during the P2 banner skips it. P2 avatar shows a spinner from end-turn click until P2 finishes its action.

---

## 6. Data Flow

New state surfaces:
- `animLockRef` (via `useActionQueue`)
- `dragRef` (replaces `dragPos` state)
- `targetingRef` (attack-arrow drag state)

Existing state retained:
- `turn`, `activePlayer`, `p1HP`, `p2HP`, `p1Morale`, `p2Morale`, `hand`, deck/discard, `board`, `turnBanner`, `endScreen`, `attacking`

Removed:
- `dragPos` (moved to ref)
- `selectedAttacker` (replaced by `targetingRef`; the click-attacker selection mode is gone)

---

## 7. Acceptance Criteria

| # | Criterion | How to verify |
|---|---|---|
| 1 | Drag does not cause React re-render storm | DevTools Performance recording: ≤2 commits per drag |
| 2 | Drag below 8px = click, not drag | Mouse down + release without moving = card stays in hand |
| 3 | Invalid drop bounces card back | Drag onto invalid slot, release → smooth 250ms return |
| 4 | ESC cancels drag | During drag, press ESC → card returns to hand |
| 5 | Hand hover does not re-fan siblings | Inspect sibling card transforms during hover; siblings unchanged |
| 6 | Hover preview large card visible | Hover a hand card, preview at top-right corner |
| 7 | Invalid slots dimmed during drag | Visible opacity difference between valid and invalid slots |
| 8 | Attack via drag arrow works | Press on P1 unit, drag to enemy, release = attack |
| 9 | Attack timing distance-aware | Long lunge visibly slower than short lunge |
| 10 | Freeze frame at impact observable | 90ms pause before recoil — visible to the eye |
| 11 | Counter staged at +220ms | Counter damage clearly arrives after impact, not simultaneously |
| 12 | Shake scales with damage | 1-HP kill ≠ 4-HP kill in shake intensity |
| 13 | No shake on routine deploy/advance | Deploy a card, no stage transform |
| 14 | Damage number overshoots | Visible bounce past target size |
| 15 | Action queue accepts mid-animation input | Click during animation, action runs after |
| 16 | Banner skippable | Press any key during banner, skips immediately |
| 17 | AI spinner visible | After end-turn, spinner shows on P2 avatar within 200ms |
| 18 | All 3 matchups still work | France/Prussia, France/Russia, Prussia/Russia matchup buttons function unchanged |
| 19 | All 4 Tweak controls still work | bgKind, mood, cardStyle, speed all functional |

---

## 8. Test Plan

This is a prototype; no automated UI tests exist. Verification is manual + visual:

- **Manual smoke checklist** (`prototypes/card-battle-visual-prototype/manual-smoke-2026-05-08.md`): one row per acceptance criterion above, dated, with pass/fail + screenshot reference.
- **Performance check:** Record a 5-second session in Chrome DevTools Performance panel. Verify drag has ≤2 React commits and frame rate stays ≥55fps on 2024-class laptops.
- **Visual diff:** capture before/after screenshots of (a) idle hand, (b) mid-drag, (c) attack mid-lunge, (d) post-impact.

---

## 9. Tuning Knobs

All tunables live in `tokens.css` as CSS variables. Designers can iterate on feel without touching JSX:

| Variable | Default | Effect |
|---|---|---|
| `--dur-snap` | 240ms | Card enters / appears |
| `--dur-rest` | 280ms | Card lands at rest |
| `--dur-overshoot` | 380ms | Impact bounce, damage number pop |
| `--dur-hover` | 150ms | Hover up/down |
| `--drag-threshold` | 8px | How far before drag lifts |
| `--bounce-back` | 250ms | Invalid drop return |
| `--ai-pause` | 800ms | AI thinking delay |
| `--banner-hold` | 600ms | Turn banner default duration |
| `--shake-base` | 4 | Base shake px |
| `--shake-per-dmg` | 1.5 | Shake px per damage point |
| `--shake-cap` | 12 | Max shake px |

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Action queue refactor cascades into existing setTimeout chains in `deployCard`/`attackTarget` | Phase 1 introduces the lock without changing internal timing; Phase 2 migrates `setTimeout` chains one function at a time, with manual smoke after each |
| Attack drag-arrow conflicts with existing click selection | Remove old click-attacker model entirely (no compatibility shim); update acceptance criterion to confirm new flow only |
| rAF + transform direct write leaks event listeners on unmount | Always pair `addEventListener` with cleanup in `useEffect` return; verify in DevTools after navigation |
| Damage shake on full stage interferes with HQ animation | Apply shake to a wrapper inside `stage` rather than `stage` itself, so HQ bars / banners are not shaken |

---

## 11. Phasing Hint For The Plan

(Detailed plan will be authored separately via writing-plans.)

- **Phase 1 — Tokens & easing palette.** Cheapest, unblocks every other phase.
- **Phase 2 — Drag rewrite + hand fan + drop-zone telegraph.** Largest single feel improvement.
- **Phase 3 — Action queue.** Foundation for Phase 4.
- **Phase 4 — Attack drag-arrow + choreography + shake scaling + damage overshoot.**
- **Phase 5 — Banner skip + AI spinner.**
- **Phase 6 — Manual smoke + tuning pass.**

---

## 12. Acceptance Bands At A Glance

| Metric | Pass |
|---|---|
| Drag React commits per second | ≤2 |
| Frame rate during full attack sequence | ≥55fps |
| Banner skippable within | 1 frame (16ms) of input |
| AI spinner appears within | 200ms of end-turn |
| All 19 acceptance criteria | Pass on manual smoke |
