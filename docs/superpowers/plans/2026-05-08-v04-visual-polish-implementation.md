# v0.4 Visual Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the React visual prototype feel fluid, responsive, and physically credible by closing the largest interaction-feel gaps.

**Architecture:** CSS token system for easing/duration variables. Ref-based drag to eliminate re-render storms. Action queue (length-1 FIFO) to accept input during animations. Staged attack choreography replacing fixed timing. All changes confined to `prototypes/card-battle-visual-prototype/`.

**Tech Stack:** React 18 (Babel standalone, no build step), CSS variables, pointer events, requestAnimationFrame, inline SVG for attack arrows.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `prototypes/card-battle-visual-prototype/tokens.css` | Create | 4 easing curves + 8 duration/interaction tokens |
| `prototypes/card-battle-visual-prototype/index.html` | Modify | Add `<link>` for tokens.css; update damage-pop keyframes |
| `prototypes/card-battle-visual-prototype/battlefield.jsx` | Modify | All interaction changes (drag, hand, attack, shake, banner) |

---

### Task 1: Tokens & Easing Palette

**Files:**
- Create: `prototypes/card-battle-visual-prototype/tokens.css`
- Modify: `prototypes/card-battle-visual-prototype/index.html:7`

- [ ] **Step 1: Create tokens.css**

```css
/* prototypes/card-battle-visual-prototype/tokens.css */
:root {
  /* 4 named curves — all animations must use one of these */
  --ease-snap-in:    cubic-bezier(0.20, 0.90, 0.30, 1.00);
  --ease-rest:       cubic-bezier(0.00, 0.00, 0.20, 1.00);
  --ease-overshoot:  cubic-bezier(0.34, 1.56, 0.64, 1.00);
  --ease-hover:      ease-in-out;

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

- [ ] **Step 2: Add link in index.html**

At line 7 of `index.html`, insert `<link rel="stylesheet" href="./tokens.css">` immediately before the existing `<style>` tag.

- [ ] **Step 3: Verify**

Open `http://localhost:8010/`, run in console:
```js
getComputedStyle(document.documentElement).getPropertyValue('--ease-snap-in')
```
Expected: `cubic-bezier(0.20, 0.90, 0.30, 1.00)`

- [ ] **Step 4: Commit**

```bash
git add prototypes/card-battle-visual-prototype/tokens.css prototypes/card-battle-visual-prototype/index.html
git commit -m "feat(v0.4): add easing/duration token system"
```

---

### Task 2: Action Queue Hook

**Files:**
- Modify: `prototypes/card-battle-visual-prototype/battlefield.jsx:1-8`

- [ ] **Step 1: Add useActionQueue hook**

Insert after line 8 (`const { useState, useEffect, useRef, useCallback } = React;`):

```js
// ─────────── Action Queue ───────────
function useActionQueue() {
  const [locked, setLocked] = useState(false);
  const pendingRef = useRef(null);

  const tryRun = useCallback((fn) => {
    if (locked) {
      pendingRef.current = fn;
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

  return { locked, tryRun };
}
```

- [ ] **Step 2: Wire into Battlefield**

Inside the `Battlefield` function, after existing refs (around line 498), add:

```js
const { locked: animLocked, tryRun: tryRunAction } = useActionQueue();
```

- [ ] **Step 3: Verify**

Open the prototype. No behavior change yet — hook is wired but not wrapping any functions. Console: no errors.

- [ ] **Step 4: Commit**

```bash
git add prototypes/card-battle-visual-prototype/battlefield.jsx
git commit -m "feat(v0.4): add useActionQueue hook"
```

---

### Task 3: Drag Rewrite

**Files:**
- Modify: `prototypes/card-battle-visual-prototype/battlefield.jsx` (lines 483-597, 954-997)
- Modify: `prototypes/card-battle-visual-prototype/tokens.css` (append drop-zone CSS)

- [ ] **Step 1: Replace drag state with refs**

At line 483-485, replace:
```js
const [draggingCard, setDraggingCard] = useState(null);
const [dragPos, setDragPos] = useState({ x: 0, y: 0 });
const [hoveredSlot, setHoveredSlot] = useState(null);
```
With:
```js
const [draggingCard, setDraggingCard] = useState(null);
const dragRef = useRef({ x: 0, y: 0, startX: 0, startY: 0, lifted: false });
const ghostRef = useRef(null);
const rafIdRef = useRef(null);
const [hoveredSlot, setHoveredSlot] = useState(null);
```

- [ ] **Step 2: Rewrite onCardMouseDown → onCardPointerDown**

Replace lines 550-556 with:
```js
function onCardPointerDown(e, card) {
  if (card.cost > p1Morale || activePlayer !== 1) return;
  if (animLocked) return;
  e.preventDefault();
  const rect = stage.current.getBoundingClientRect();
  dragRef.current = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
    startX: e.clientX,
    startY: e.clientY,
    lifted: false,
  };
  setDraggingCard(card);
}
```

- [ ] **Step 3: Rewrite drag useEffect (pointer events + rAF + threshold + bounce-back)**

Replace lines 558-597 with:
```js
useEffect(() => {
  if (!draggingCard) return;
  stage.current?.classList.add('drag-active');

  function onMove(e) {
    const rect = stage.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    if (!dragRef.current.lifted) {
      if (Math.hypot(dx, dy) <= 8) return;
      dragRef.current.lifted = true;
    }
    dragRef.current.x = x;
    dragRef.current.y = y;
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    rafIdRef.current = requestAnimationFrame(() => {
      if (ghostRef.current) {
        ghostRef.current.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) rotate(-2deg) scale(1.1)`;
      }
    });
    const el = document.elementFromPoint(e.clientX, e.clientY);
    const slot = el?.closest('[data-slot]');
    const prev = hoveredSlotRef.current;
    const next = slot ? { line: slot.dataset.line, idx: parseInt(slot.dataset.idx) } : null;
    if (prev && (!next || prev.line !== next.line || prev.idx !== next.idx)) {
      const prevEl = document.querySelector(`[data-slot][data-line="${prev.line}"][data-idx="${prev.idx}"]`);
      if (prevEl) prevEl.classList.remove('slot-hover-valid');
    }
    if (next && canP1Deploy(next.line)) {
      slot.classList.add('slot-hover-valid');
    }
    hoveredSlotRef.current = next;
  }

  function onUp(e) {
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    if (!dragRef.current.lifted) { cleanup(); return; }
    const el = document.elementFromPoint(e.clientX, e.clientY);
    const slot = el?.closest('[data-slot]');
    const dropSlot = slot ? { line: slot.dataset.line, idx: parseInt(slot.dataset.idx) } : hoveredSlotRef.current;
    if (dropSlot && draggingCard && canP1Deploy(dropSlot.line)) {
      const slotData = board[dropSlot.line][dropSlot.idx];
      if (!slotData) { deployCard(draggingCard, dropSlot.line, dropSlot.idx); cleanup(); return; }
    }
    // Bounce-back
    if (ghostRef.current) {
      const handCard = document.querySelector(`[data-hand-card="${draggingCard.id}"]`);
      if (handCard) {
        const cr = handCard.getBoundingClientRect();
        const sr = stage.current.getBoundingClientRect();
        const tx = cr.left + cr.width/2 - sr.left;
        const ty = cr.top + cr.height/2 - sr.top;
        ghostRef.current.style.transition = `transform 250ms var(--ease-rest)`;
        ghostRef.current.style.transform = `translate(${tx}px, ${ty}px) translate(-50%, -50%) rotate(0deg) scale(1.0)`;
        setTimeout(() => cleanup(), 250);
        return;
      }
    }
    cleanup();
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      cleanup();
    }
  }

  function cleanup() {
    document.querySelectorAll('.slot-hover-valid').forEach(el => el.classList.remove('slot-hover-valid'));
    hoveredSlotRef.current = null;
    setDraggingCard(null);
    stage.current?.classList.remove('drag-active');
  }

  window.addEventListener('pointermove', onMove);
  window.addEventListener('pointerup', onUp);
  window.addEventListener('keydown', onKeyDown);
  return () => {
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);
    window.removeEventListener('keydown', onKeyDown);
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    stage.current?.classList.remove('drag-active');
  };
}, [draggingCard, board, p1Morale, activePlayer, deployCard, canP1Deploy]);
```

- [ ] **Step 4: Wrap deployCard with action queue**

Replace `deployCard` (lines 599-639) to use `tryRunAction`. The function body stays the same but is wrapped:
```js
function deployCard(card, line, idx) {
  tryRunAction((done) => {
    // ... existing deployCard body unchanged ...
    // At the end of the last setTimeout (line 638), call done():
    setTimeout(() => {
      setBoard(b => {
        const ln = b[line].map(u => u?.id === card.id ? { ...u, justDeployed: false } : u);
        return { ...b, [line]: ln };
      });
      done();
    }, 700 / speed);
  });
}
```

- [ ] **Step 5: Update ghost element to use ref**

Replace the dragging ghost JSX (lines 987-997):
```jsx
{draggingCard && (
  <div ref={ghostRef} style={{
    position: 'absolute', left: 0, top: 0,
    transform: `translate(${dragRef.current.x}px, ${dragRef.current.y}px) translate(-50%, -50%) rotate(-2deg) scale(1.1)`,
    pointerEvents: 'none', zIndex: 999,
    filter: 'drop-shadow(0 16px 30px rgba(0,0,0,0.7))',
    willChange: 'transform',
  }}>
    <window.Card style={cardStyle} unit={draggingCard} faction={draggingCard.faction} onCard/>
  </div>
)}
```

- [ ] **Step 6: Update hand card handler**

In the hand card rendering (line 979), change `onMouseDown` to `onPointerDown`:
```jsx
onPointerDown={(e) => onCardPointerDown(e, card)}
```

- [ ] **Step 7: Append drop-zone CSS to tokens.css**

Append to `tokens.css`:
```css
/* Drop-zone telegraph */
.battlefield-stage.drag-active [data-slot] {
  opacity: 0.4;
  transition: opacity 0.15s;
}
.battlefield-stage.drag-active [data-slot].slot-hover-valid {
  opacity: 1;
  box-shadow: inset 0 0 12px rgba(212,165,92,0.4), 0 0 16px rgba(212,165,92,0.6);
  border-color: #d4a55c;
}
```

- [ ] **Step 8: Verify**

Drag a card slowly — below 8px nothing happens. Drag beyond 8px — ghost follows cursor smoothly. Drop on valid p1rear slot — deploys. Drop on invalid slot — bounces back 250ms. Press ESC — returns to hand. During drag: valid slots glow gold, invalid slots dimmed.

- [ ] **Step 9: Commit**

```bash
git add prototypes/card-battle-visual-prototype/tokens.css prototypes/card-battle-visual-prototype/battlefield.jsx
git commit -m "feat(v0.4): rewrite drag with pointer events, rAF, threshold, bounce-back, drop-zone telegraph"
```

---

### Task 4: Hand Fan Polish

**Files:**
- Modify: `prototypes/card-battle-visual-prototype/battlefield.jsx:954-985`

- [ ] **Step 1: Dynamic angle + hover scale**

Replace the angle/offY calculation (around line 956):
```js
const N = hand.length;
const angle = (i - (N-1)/2) * Math.min(8, 70 / N);
const offY = Math.abs(i - (N-1)/2) * Math.min(6, 42 / N);
const isHovered = hoveredHandIndex === i && !draggingCard;
```

Change hover scale from 1.25 to 1.45 in the transform (line 969):
```js
transform: `translateY(${card.drawing ? 200 : (isHovered ? -78 : offY)}px) rotate(${isHovered ? 0 : angle}deg) scale(${isHovered ? 1.45 : 1})`,
```

- [ ] **Step 2: Add large card preview**

After the hand div (around line 985), before the dragging ghost:
```jsx
{hoveredHandIndex >= 0 && !draggingCard && hand[hoveredHandIndex] && (
  <div style={{
    position: 'absolute', right: 220, top: 80,
    zIndex: 200, pointerEvents: 'none',
    transform: 'scale(2.2)', transformOrigin: 'top right',
    filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.8))',
    transition: 'opacity var(--dur-hover) var(--ease-hover)',
  }}>
    <window.Card style={cardStyle} unit={hand[hoveredHandIndex]} faction={hand[hoveredHandIndex].faction} onCard/>
  </div>
)}
```

- [ ] **Step 3: Verify**

Hover hand cards — hovered card lifts 1.45×, siblings don't move. Large 2.2× preview at top-right. 7-card fan spans ~70°.

- [ ] **Step 4: Commit**

```bash
git add prototypes/card-battle-visual-prototype/battlefield.jsx
git commit -m "feat(v0.4): polish hand fan with dynamic angle, hover zoom, large preview"
```

---

### Task 5: Attack Drag-Arrow

**Files:**
- Modify: `prototypes/card-battle-visual-prototype/battlefield.jsx` (remove selectedAttacker, add targeting)

- [ ] **Step 1: Remove old click-attack model**

Delete `selectedAttacker` state (line 492). Delete `handleUnitClick` (lines 641-656). Delete `handleHqClick` (lines 697-700). Delete `canAdvanceSelectedTo` (lines 664-670). Delete `advanceSelectedTo` (lines 672-695).

- [ ] **Step 2: Add targeting refs**

After the action queue declaration:
```js
const targetingRef = useRef(null);
const arrowRef = useRef(null);
```

- [ ] **Step 3: Add advanceUnit function**

```js
function advanceUnit(fromLine, fromIdx, toLine, toIdx) {
  tryRunAction((done) => {
    setBoard(b => {
      const unit = b[fromLine][fromIdx];
      if (!unit || b[toLine][toIdx]) return b;
      const from = [...b[fromLine]];
      const to = [...b[toLine]];
      from[fromIdx] = null;
      to[toIdx] = { ...unit, justDeployed: false, hasAdvanced: true };
      return { ...b, [fromLine]: from, [toLine]: to };
    });
    setP1Morale(m => Math.max(0, m - 1));
    setTimeout(() => {
      const slotEl = document.querySelector(`[data-slot][data-line="${toLine}"][data-idx="${toIdx}"]`);
      if (slotEl && stage.current) {
        const r = slotEl.getBoundingClientRect();
        const sr = stage.current.getBoundingClientRect();
        spawnParticle(fxLayer.current, r.left+r.width/2-sr.left, r.top+r.height/2-sr.top, 'flash');
      }
      done();
    }, 40);
  });
}
```

- [ ] **Step 4: Add attack targeting useEffect**

```js
useEffect(() => {
  if (animLocked || activePlayer !== 1) return;
  function onPointerDown(e) {
    const slot = e.target.closest('[data-slot]');
    if (!slot) return;
    const line = slot.dataset.line;
    const idx = parseInt(slot.dataset.idx);
    const unit = board[line]?.[idx];
    if (!unit || unit.owner !== 'p1' || unit.hasAdvanced) return;
    e.preventDefault();
    const rect = stage.current.getBoundingClientRect();
    targetingRef.current = { line, idx, originX: e.clientX - rect.left, originY: e.clientY - rect.top };
    if (arrowRef.current) arrowRef.current.style.display = 'block';
  }
  function onPointerMove(e) {
    if (!targetingRef.current) return;
    const rect = stage.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const { originX, originY } = targetingRef.current;
    const svg = arrowRef.current;
    if (svg) {
      const path = svg.querySelector('path');
      const cpX = (originX + x) / 2;
      const cpY = Math.min(originY, y) - 30;
      path.setAttribute('d', `M${originX},${originY} Q${cpX},${cpY} ${x},${y}`);
    }
  }
  function onPointerUp(e) {
    if (!targetingRef.current) return;
    const { line, idx } = targetingRef.current;
    if (arrowRef.current) arrowRef.current.style.display = 'none';
    const el = document.elementFromPoint(e.clientX, e.clientY);
    const slot = el?.closest('[data-slot]');
    const hq = el?.closest('[data-hq]');
    if (hq?.dataset.hq === 'p2') {
      attackTarget(line, idx, null, null);
    } else if (slot) {
      const tl = slot.dataset.line;
      const ti = parseInt(slot.dataset.idx);
      const tu = board[tl]?.[ti];
      if (tu?.owner === 'p2') {
        attackTarget(line, idx, tl, ti);
      } else if (!tu) {
        const nextLine = nextP1Line(line);
        if (nextLine === tl && idx === ti && p1Morale >= 1) {
          advanceUnit(line, idx, tl, ti);
        }
      }
    }
    targetingRef.current = null;
  }
  function onCancel() {
    targetingRef.current = null;
    if (arrowRef.current) arrowRef.current.style.display = 'none';
  }
  const el = stage.current;
  if (!el) return;
  el.addEventListener('pointerdown', onPointerDown);
  window.addEventListener('pointermove', onPointerMove);
  window.addEventListener('pointerup', onPointerUp);
  window.addEventListener('pointercancel', onCancel);
  return () => {
    el.removeEventListener('pointerdown', onPointerDown);
    window.removeEventListener('pointermove', onPointerMove);
    window.removeEventListener('pointerup', onPointerUp);
    window.removeEventListener('pointercancel', onCancel);
  };
}, [animLocked, activePlayer, board, p1Morale, attackTarget, advanceUnit]);
```

- [ ] **Step 5: Add SVG arrow element**

After the fxLayer div (around line 1019):
```jsx
<svg ref={arrowRef} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 55, display: 'none' }}>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#d4a55c" opacity="0.9"/>
    </marker>
  </defs>
  <path d="" fill="none" stroke="#d4a55c" strokeWidth="2.5" strokeDasharray="8,4" markerEnd="url(#arrowhead)" opacity="0.8"/>
</svg>
```

- [ ] **Step 6: Remove selectedAttacker references from Line/Slot/HQBar**

Remove `selectedAttacker`, `canAdvanceTo`, `onSlotClick` props from Line. Remove `selected`, `advanceTarget`, `onSlotClick` from Slot. Remove `targetable`/`onClick` from P2 HQBar. Simplify Slot styling accordingly.

- [ ] **Step 7: Verify**

Press P1 unit, drag — dashed golden arrow follows cursor. Release on enemy — attack. Release on empty next-line slot — advance. Release on empty space — cancel. ESC — cancel.

- [ ] **Step 8: Commit**

```bash
git add prototypes/card-battle-visual-prototype/battlefield.jsx
git commit -m "feat(v0.4): replace click-attack with drag-arrow (Hearthstone-style)"
```

---

### Task 6: Attack Choreography

**Files:**
- Modify: `prototypes/card-battle-visual-prototype/battlefield.jsx` (attackTarget internals)

- [ ] **Step 1: Replace fixed 280ms with staged timeline**

Inside `attackTarget`'s `tryRunAction` callback, replace the single `setTimeout` at 280ms with:

```js
// Stage 0: wind-up (0..80ms)
const unitEl = slotEl.querySelector('[style]');
if (unitEl) {
  unitEl.style.transition = `transform 80ms var(--ease-snap-in)`;
  unitEl.style.transform = `scale(0.95) rotate(${dx > 0 ? -5 : 5}deg)`;
}

// Stage 1: lunge (80..80+L ms)
const L = Math.min(380, 240 + dist / 3);
setTimeout(() => {
  setAttacking({ line, idx, dx: dx * 0.55, dy: dy * 0.55 });
  if (unitEl) { unitEl.style.transition = `transform ${L}ms var(--ease-overshoot)`; unitEl.style.transform = ''; }
}, 80 / speed);

// Stage 2: freeze + impact (80+L ms)
setTimeout(() => {
  const impactX = a.left + a.width/2 + dx*0.55 - sr.left;
  const impactY = a.top + a.height/2 + dy*0.55 - sr.top;
  spawnParticle(fxLayer.current, impactX, impactY, 'flash');
  for (let i = 0; i < 12; i++) spawnParticle(fxLayer.current, impactX, impactY, 'spark');
  for (let i = 0; i < 6; i++) {
    setTimeout(() => spawnParticle(fxLayer.current, impactX + (Math.random()-0.5)*30, impactY + (Math.random()-0.5)*30, 'smoke'), i*50);
  }
  const dmg = unit.atk;
  spawnParticle(fxLayer.current, impactX, impactY, 'damage', '-' + dmg);
  // Shake + damage application here (see Task 7 for shake scaling)
  setShake(true); setFlash(true);
  setTimeout(() => { setShake(false); setFlash(false); }, 200);
  // ... damage logic (same as current) ...
}, (80 + L) / speed);

// Stage 3: recoil (170+L ms)
setTimeout(() => { setAttacking(null); }, (170 + L) / speed);

// Stage 4: counter (390+L ms)
// ... counter logic (same as current, but at 390+L instead of 100) ...

// Done
setTimeout(() => { done(); }, (590 + L) / speed);
```

- [ ] **Step 2: Verify**

Attack far unit — lunge visibly longer than near unit. Freeze frame at impact observable (~90ms). Counter arrives clearly after initial impact.

- [ ] **Step 3: Commit**

```bash
git add prototypes/card-battle-visual-prototype/battlefield.jsx
git commit -m "feat(v0.4): staged attack choreography with distance-aware lunge"
```

---

### Task 7: Shake Scaling + Damage Overshoot

**Files:**
- Modify: `prototypes/card-battle-visual-prototype/battlefield.jsx` (shake state)
- Modify: `prototypes/card-battle-visual-prototype/index.html` (damage keyframes)

- [ ] **Step 1: Replace boolean shake with shakeAmp**

Replace `const [shake, setShake] = useState(false)` with `const [shakeAmp, setShakeAmp] = useState(0)`.

Update stage transform (line 868):
```js
transform: shakeAmp > 0 ? `translate(${(Math.random()-0.5)*shakeAmp}px,${(Math.random()-0.5)*shakeAmp}px)` : 'none',
```

Update className to include `drag-active`:
```js
className={'battlefield-stage' + (shakeAmp > 0 ? ' shake' : '') + (draggingCard ? ' drag-active' : '')}
```

In attackTarget's impact stage, replace `setShake(true/false)` with:
```js
const amp = Math.min(12, 4 + dmg * 1.5);
setShakeAmp(amp);
setTimeout(() => setShakeAmp(0), 200);
```

- [ ] **Step 2: Update damage number animation**

In `index.html`, replace `damage-pop` keyframes (lines 30-35):
```css
@keyframes damage-pop {
  0%   { opacity: 0; transform: translate(-50%,-50%) scale(0.3); }
  25%  { opacity: 1; transform: translate(-50%,-50%) scale(1.45); }
  50%  { opacity: 1; transform: translate(-50%,-50%) scale(1.0); }
  100% { opacity: 0; transform: translate(-50%, calc(-50% - 50px)) scale(0.8); }
}
```

In `spawnParticle` damage branch (line 417), change animation duration from 1s to 0.7s.

- [ ] **Step 3: Verify**

Kill 1-HP unit — subtle shake ~5.5px. Kill 4-HP unit — strong shake ~10px. Deploy — no shake. Damage numbers bounce past target size.

- [ ] **Step 4: Commit**

```bash
git add prototypes/card-battle-visual-prototype/index.html prototypes/card-battle-visual-prototype/battlefield.jsx
git commit -m "feat(v0.4): shake scaling by damage + damage number overshoot"
```

---

### Task 8: Banner Skip + AI Spinner

**Files:**
- Modify: `prototypes/card-battle-visual-prototype/battlefield.jsx` (TurnBanner, endTurn, HQBar)

- [ ] **Step 1: Make TurnBanner skippable**

Add `onSkip` prop to TurnBanner. Set `pointerEvents: 'auto'` and `cursor: 'pointer'`. Add `onClick={onSkip}`.

- [ ] **Step 2: Reduce delays**

In `endTurn`: AI delay from 1500/speed → 800/speed. Banner hold: explicit 600ms with skip.

- [ ] **Step 3: Add AI spinner**

Add `spinner` prop to HQBar. Render a small CSS rotating ring next to crest when true. Add `@keyframes spin { to { transform: rotate(360deg); } }` to tokens.css.

Pass `spinner={activePlayer===2 && !turnBanner}` to P2 HQBar.

- [ ] **Step 4: Verify**

Banner 600ms then disappears. Click/key during banner — skips. P2 avatar shows spinner during AI turn. AI deploys after 800ms.

- [ ] **Step 5: Commit**

```bash
git add prototypes/card-battle-visual-prototype/tokens.css prototypes/card-battle-visual-prototype/battlefield.jsx
git commit -m "feat(v0.4): skippable banner, AI spinner, reduced delays"
```

---

### Task 9: Manual Smoke Test

**Files:**
- Create: `prototypes/card-battle-visual-prototype/manual-smoke-2026-05-08.md`

- [ ] **Step 1: Create and run checklist**

Create the file with 19 rows matching the spec's acceptance criteria. Open prototype at `http://localhost:8010/`. Test each criterion. Fill Pass/Fail.

- [ ] **Step 2: Commit**

```bash
git add prototypes/card-battle-visual-prototype/manual-smoke-2026-05-08.md
git commit -m "test(v0.4): manual smoke test results"
```

---

## Tuning Knobs Reference

All tunables in `tokens.css`:

| Variable | Default | Effect |
|----------|---------|--------|
| `--dur-snap` | 240ms | Card enters / appears |
| `--dur-rest` | 280ms | Card lands at rest |
| `--dur-overshoot` | 380ms | Impact bounce, damage pop |
| `--dur-hover` | 150ms | Hover up/down |
| `--drag-threshold` | 8px | Drag lift distance |
| `--bounce-back` | 250ms | Invalid drop return |
| `--ai-pause` | 800ms | AI thinking delay |
| `--banner-hold` | 600ms | Banner duration |
| `--shake-base` | 4 | Base shake px |
| `--shake-per-dmg` | 1.5 | Shake per damage point |
| `--shake-cap` | 12 | Max shake px |
