# KARDS-Inspired Napoleonic Battle System

**Status**: Implementation Baseline  
**Last Updated**: 2026-07-16

## Overview

The Unity vertical slice replaces the prototype's five-row march with a faster KARDS-inspired battlefield: each player owns a four-slot support line and both contest one five-slot frontline. Deployment and unit operation share the same growing Credit pool, so every turn asks whether to reinforce, move, attack, or issue an event. The structure is inspired by KARDS, while rules, terminology, art, card data, and Napoleonic systems remain original to NapoleonGame.

## Player Fantasy

The player is a Napoleonic field commander converting limited command capacity into battlefield pressure. Infantry secures the line, cavalry exploits a broken front, artillery projects power from support, skirmishers screen attacks, commanders create one decisive tempo swing, and damaged formations may become Shaken.

## Detailed Rules

- Match: one human versus one seeded AI; France, Prussia, and Russia starter decks contain the existing 33-card catalogs.
- Battlefield: each side has four Support slots; the shared Frontline has five slots and can contain units from only one side at a time.
- Frontline control: a side controls it while it has at least one unit there. The opposing side cannot move into it until all controlling units leave or are destroyed.
- Turn start: increase maximum Credits by 1 to a cap of 12, refill current Credits, ready surviving units, recover eligible Shaken units, then draw one card.
- Opening: first player draws 4 cards, second player draws 5. Hand limit is 9. Failed draws from an empty deck deal escalating fatigue damage (1, then 2, then 3, and so on).
- Unit cards pay `deployCost` to enter an empty friendly Support slot. Event cards pay their cost, resolve, and enter discard.
- Every unit has `operationCost`. Moving Support→Frontline or initiating an attack pays that cost and exhausts the unit. A unit normally performs at most one operation per owner turn.
- A newly deployed unit is exhausted until the next owner turn unless it has `冲锋`.
- Targeting: Support units may attack enemy Frontline units. Frontline units may attack enemy Support units or HQ when the enemy does not occupy the Frontline. `远程` and `侧翼迂回` extend targeting as described by their tooltips.
- Combat resolves attacker damage, survival, then counter-damage unless the attacker is `远程`. `守卫` restricts legal targets. `结阵`, `齐射`, `闪避`, `突破`, `动摇`, and faction keywords remain explicit rule modifiers.
- HQ starts at 20 HP. A player wins immediately when the opposing HQ reaches 0 or less. Hard timeout is 30 full rounds; higher HQ wins, equal HQ is a draw.
- Turn actions are freely interleaved. There are no separate deploy/move/attack phases; the End Turn command is always available when animations are idle.
- The first vertical slice includes no opponent reaction windows, countermeasure stack, online PvP, deck builder, rarity, packs, or monetization.

## Formulas

- `maxCredits = min(previousMaxCredits + 1, 12)`.
- Default `operationCost`: Infantry/Skirmisher 1; Cavalry/Artillery/Guard 2. Card data may override later.
- `effectiveAttack = max(0, baseAttack + liveBonuses - livePenalties - (Shaken ? 1 : 0))`.
- Cavalry versus unformed Infantry/Guard: `damage = 2 × effectiveAttack`.
- Cavalry versus formed Infantry/Guard: `damage = max(1, floor(effectiveAttack / 2))`; `突破` ignores this reduction.
- Artillery versus Infantry/Guard: `damage = effectiveAttack + (formed ? 2 : 1)`.
- Otherwise: `damage = effectiveAttack`.
- Counter-damage is defender base attack, or half when defender is Artillery; `远程` attackers receive no counter.
- Shaken trigger: a surviving unit taking at least 2 damage becomes Shaken when current HP is at or below half base max HP.
- Fatigue on the Nth failed draw deals N HQ damage.

## Edge Cases

- A full Support line rejects deployment without spending Credits or discarding the card.
- A full Frontline rejects movement without spending Credits or exhausting the unit.
- Illegal drops snap back and show a short reason before any command is dispatched.
- A unit reduced to 0 HP is removed before control and legal-target state are recalculated.
- If both HQs reach 0 in one atomic combat resolution, the result is a draw.
- Events with no legal target stay in hand and spend no Credits.
- Shaken never stacks, dead units cannot become Shaken, and recovery is deterministic.
- Animation cancellation or reduced-motion mode cannot alter domain state; visuals reconcile from the authoritative snapshot.

## Dependencies

- Card source: `prototypes/card-battle-sim/cards.py` exported into the Unity catalog.
- Balance oracle: Python simulator tests and deterministic ecosystem runner.
- Technical architecture: `docs/architecture/adr-0001-unity-client-architecture.md`.
- Interaction reference: `docs/product/card-game-ui-interaction-research-report.md`.
- Unity project: `src/NapoleonGame.Unity/`.

## Tuning Knobs

- HQ HP, Credit cap, draw rate, hand limit, fatigue growth, Support/Frontline capacity.
- Per-card deploy and operation costs.
- Keyword modifiers, Shaken threshold, and recovery timing.
- AI action scoring and think delay.
- Animation durations, input lock, camera shake, and reduced-motion scale.

## Acceptance Criteria

- A human can start any faction matchup, deploy, move, attack, play supported events, end turns, and reach a result against AI.
- The UI previews legal targets and explains illegal actions before state changes.
- Same seed and command sequence produce identical domain snapshots.
- Unity EditMode tests cover economy, Frontline control, targeting, combat, fatigue, Shaken, victory, and AI match completion.
- All three starter decks load 33 cards and every displayed card shows deploy cost, operation cost, stats/type, rules text, and original faction styling.
- Deploy, move, attack, damage, death, turn, and victory feedback are visible; reduced-motion mode remains fully playable.

