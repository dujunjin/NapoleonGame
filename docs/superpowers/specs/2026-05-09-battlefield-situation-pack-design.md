# NapoleonGame v0.5 Battlefield Situation Pack Product Design

**Status:** Draft — pending Oracle review  
**Date:** 2026-05-09  
**Perspective:** Product design for a low-risk gameplay expansion to the current `prototypes/card-battle-sim/` rules simulator.  
**Baseline:** Current active simulator has 3 factions, 33 cards/faction, HQ 14, three-line battlefield, command layer, tactical objectives, v0.3B triggers/subfactions, and v0.4 Shaken morale marker. Balance gates remain PacingRisk <= 0.30, faction win rates roughly 45%-55%, mirror first-player <= 65%.

---

## 1. Goal And Scope

The Battlefield Situation Pack makes each match feel more like a changing Napoleonic battle without rewriting the core card loop.

Product question:

> Can two matches with the same factions produce meaningfully different battlefield stories while staying readable and balance-testable?

**In scope:**

- 4 public battlefield situations that rotate deterministically during the match
- 3 commander reaction abilities, one per faction
- 2 MVP unit-synergy rules for infantry/artillery/cavalry identity, with Skirmisher Hold deferred
- A small Shaken-pressure extension that uses the existing `is_shaken` state
- Replay/export support so every situation and reaction is visible in logs/viewer data
- Focused unit tests and ecosystem balance checks

**Out of scope:**

- Adding a new faction
- Changing 33-card deck counts
- Changing HQ start HP
- Adding hidden information
- Adding interrupt/reaction windows controlled by player input
- Replacing current commanders/objectives
- Large AI rewrite; only heuristic awareness for new public rules is allowed

---

## 2. Design Pillars

1. **Public battlefield drama, not hidden complexity.** Every new modifier must be visible in logs and replay state.
2. **Weather and ground should change plans, not decide games.** Situations are mild constraints or small bonuses, never match-ending swings.
3. **Use existing seams.** Prefer `commanders.py`, `triggers.py`, `combat.py`, `game_state.py`, and additive export metadata over core loop rewrites.
4. **Faction identity stays readable.** France rewards tempo, Prussia rewards formation resilience, Russia rewards attrition survival.
5. **Balance gates stay authoritative.** If a cool rule breaks pacing or faction win-rate bands, tune or cut it.

---

## 3. Feature Overview

The pack has four linked but independently testable layers:

| Layer | Player-facing name | System purpose |
|---|---|---|
| Battlefield Situations | 战场态势 | Adds match-to-match variation through public temporary global rules |
| Commander Reactions | 指挥官反应 | Gives each commander one automatic dramatic identity moment |
| Unit Synergies | 兵种协同 | Makes infantry/artillery/cavalry/skirmisher combinations matter more |
| Shaken Pressure | 士气压力 | Extends current Shaken marker without creating a full morale economy |

Recommended MVP implementation order:

1. Battlefield Situations only
2. Commander Reactions
3. Unit Synergies
4. Shaken Pressure

Each layer should pass tests and balance checks before the next layer is enabled.

### 3.1 Feature Flags

Each layer must be independently gated for balance isolation and rollback:

```python
ENABLE_BATTLEFIELD_SITUATIONS = False
ENABLE_COMMANDER_REACTIONS = False
ENABLE_UNIT_SYNERGIES = False
ENABLE_SHAKEN_PRESSURE = False
```

Implementation plans may enable one flag at a time during development, but the default branch should not enable later layers until their tests and ecosystem checks pass.

---

## 4. Battlefield Situations 战场态势

### 4.1 Timing

- A battlefield situation is public and global.
- First situation appears at the start of full round 3.
- A new situation appears every 3 full rounds: 3, 6, 9, 12, 15, etc.
- A situation lasts until the next situation appears.
- Situation order is deterministic from the match seed.
- A situation may not repeat until all 4 have appeared once.

Definition of “full round”: both players receive their normal action opportunity before victory settlement, consistent with existing full-round victory rules.

### 4.2 Situation Set

#### 1. 浓雾 Dense Fog

**Rule:** Units with `远程` deal -1 damage when attacking units or HQ, minimum 1 damage after all modifiers.

**Purpose:** Temporarily weakens artillery/HQ reach without shutting it off.

**Notes:**
- Does not affect non-ranged attackers.
- Does not reduce counterattack damage unless the counterattacker is also using `远程`.

#### 2. 泥泞 Mud

**Rule:** Cavalry units cost +1 order to advance while Mud is active.

**Purpose:** Slows cavalry tempo using the simulator's current one-line advance model.

**Notes:**
- This applies to normal cavalry advance from rear→main and main→skirmish.
- It does not prevent cavalry from attacking.
- It does not change cavalry card deployment cost.
- If an effect advances a cavalry unit for free, Mud blocks the free advance unless the effect explicitly says it ignores terrain.

#### 3. 炮烟 Cannon Smoke

**Rule:** The first attack each player makes during their action phase cannot trigger `齐射` bonus damage.

**Purpose:** Creates small sequencing decisions and weakens opening volley turns.

**Notes:**
- Only suppresses `齐射`; other On Attack effects still resolve.
- Each player has their own first-attack check.
- This requires tracking `attacks_made_this_action` per player action. It does not reuse `attacker.has_acted_this_turn`, because current `齐射` is unit-first-attack based.

#### 4. 补给线稳定 Stable Supply Lines

**Rule:** At the start of each player action while this situation is active, that player gains +1 current order for this action only, capped by the global hard cap (`MAX_ORDERS`), not by that player's current `max_orders`.

**Purpose:** Creates a tempo-positive situation that speeds deployment and movement.

**Notes:**
- The bonus may allow `current_orders` to be `max_orders + 1` for this action.
- It does not increase `max_orders`.
- It is not stored between actions; the normal start-of-action order reset remains authoritative.
- If temporary order plumbing proves risky, fallback: first deploy or advance action this player takes costs 1 less, minimum 0.

### 4.3 Data Model

Add public state:

```python
Battlefield.current_situation_id: Optional[str]
Battlefield.current_situation_started_turn: int
Battlefield.situation_cycle: list[str]
```

Export additive metadata:

```json
"battlefield_situation": {
  "id": "dense_fog",
  "name": "浓雾",
  "started_turn": 3,
  "remaining_rounds_estimate": 2
}
```

Missing metadata must not break older viewer data.

---

## 5. Commander Reactions 指挥官反应

### 5.1 General Rules

- Each commander has one reaction per match.
- Reactions are automatic, public, and logged.
- Reactions do not require player input and do not create interrupts.
- Reactions may fire during either player’s action, depending on trigger.
- A reaction cannot fire if its commander has already used this reaction.
- Existing active commander ability remains separate unless implementation chooses to share a `used_reaction` field.

### 5.2 France — 拿破仑: 战机捕捉

**Trigger:** First time a French unit triggers `突破` or deals HQ damage.  
**Effect:** France gains +1 order immediately, capped normally.  
**Fantasy:** Napoleon converts local success into operational momentum.

### 5.3 Prussia — 布吕歇尔: 顽强集结

**Trigger:** First time Prussia’s main line becomes empty due to enemy attack or destruction.  
**Effect:** If Prussia has an empty rear slot, create a public token unit there: `后备国民军` (Prussia, 线列步兵, 1 attack, 2 HP, cost 0, tags: `landwehr`, `token`). If no rear slot exists, Prussia gains +1 order instead.  
**Fantasy:** Prussian resilience and late rally.

**Safety note:** The token is not drawn from deck or discard and never enters the discard pile as a card. This avoids duplicating a living card instance from `discard_pile`.

### 5.4 Russia — 库图佐夫: 深纵回撤

**Trigger:** First time Russia HQ takes damage.  
**Effect:** Heal 1 HP to the most damaged surviving Russian unit. If no damaged unit exists, Russia HQ heals 1, not exceeding starting HQ HP.  
**Fantasy:** Russia absorbs pressure and trades space for endurance.

### 5.5 Data Model

Add to commander runtime state:

```python
reaction_used: bool = False
reaction_turn: int = 0
```

Export additive metadata on steps where a reaction fires:

```json
"commander_reaction": {
  "commander": "拿破仑",
  "reaction_id": "opportunity_seized",
  "effect_text": "+1 军令"
}
```

---

## 6. Unit Synergies 兵种协同

Synergy rules are passive public checks. They should be implemented as simple combat/deploy/turn-state checks, not as new card text on individual cards.

### 6.1 Infantry + Artillery: 炮步协同

**Condition:** A player has an infantry and artillery unit in the same slot index across main/rear lines.  
**Effect:** The artillery’s first attack each turn deals +1 damage, only against units, not HQ.  
**Purpose:** Rewards classic line-and-gun positioning without increasing HQ burst.

### 6.2 Cavalry vs Shaken: 追击溃兵

**Condition:** Cavalry attacks a Shaken unit.  
**Effect:** +1 damage to defender.  
**Purpose:** Makes Shaken tactically relevant and gives cavalry a clear finisher role.

### 6.3 Deferred: Skirmisher Hold / 散兵压制

Skirmisher Hold is **deferred from MVP**. The first draft only modified HQ threat estimate, which is UI/AI metadata rather than player-facing gameplay.

Future redesign options:

- A skirmisher that starts and ends its owner action in skirmish causes the opponent's first advance next action to cost +1.
- A skirmisher that holds skirmish for a full round grants +1 order next action.
- A skirmisher in uncontested skirmish enables a future objective reward.

### 6.4 Guard Rails

- Synergy bonuses stack with existing card effects unless explicitly capped.
- A unit may benefit from at most one synergy damage bonus per attack.
- Synergy bonuses must be visible in combat logs.
- MVP synergies are limited to Infantry + Artillery and Cavalry vs Shaken.

---

## 6A. Damage Modifier Order And Edge Cases

All damage-affecting rules must resolve in deterministic order:

1. Base effective attack after current unit states, including Shaken attack penalty.
2. Built-in keyword/card modifiers (`齐射`, `结阵`, existing weather event card modifiers, etc.).
3. Battlefield situation modifiers (`浓雾`, `炮烟`).
4. Unit synergy modifiers (`炮步协同`, `追击溃兵`).
5. Defensive prevention/replacement such as `闪避`.
6. Final damage clamp.

Specific edge-case rules:

- `闪避` may still reduce final damage to 0. Dense Fog's “minimum 1” does not override evasion.
- Dense Fog only reduces positive ranged damage. If an attack's current damage is already 0, Dense Fog does nothing.
- Dense Fog stacks with existing weather event cards unless a specific card says otherwise.
- Cannon Smoke suppresses only the `齐射` bonus on that player's first attack during the action. It does not suppress other On Attack triggers.
- If Dense Fog and Cavalry vs Shaken both somehow apply to the same attack in a future rule extension, apply Dense Fog first, then synergy.

---

## 7. Shaken Pressure 士气压力

This is a small extension to v0.4 Shaken, not a full morale resource.

### 7.1 Pressure Conditions

A player is under morale pressure if either is true:

- Their HQ is at 7 HP or lower.
- They lost 2 or more units during the current full round.

Unit-loss count includes units destroyed by attacks, counterattacks, and event effects. It does **not** include self-damage that does not destroy a unit, temporary tokens leaving play by rule cleanup, or units that were already at 0 HP before the current full round.

### 7.2 Rule

While under morale pressure, a surviving unit becomes Shaken after taking 1+ damage if it is at half HP or lower.

Current baseline requires surviving at half HP or less after taking at least 2 damage. This rule lowers only the damage threshold under pressure.

Pressure is checked after damage is applied but before the Shaken decision for that damage event. If the damage itself lowers HQ to 7 or destroys the second unit this full round, subsequent damage events use the pressure threshold; the current damage event uses pressure only if the condition was already true before that event.

### 7.3 Recovery

Recovery remains unchanged: Shaken clears at owner turn end unless a future design changes it.

### 7.4 Guard Rails

- No random morale checks.
- No persistent morale meter in MVP.
- No hidden morale state; pressure condition is derived from public HQ/unit-loss data.
- Shaken Pressure ships last and remains behind `ENABLE_SHAKEN_PRESSURE` until ecosystem tests confirm Shaken frequency remains acceptable.
- Tuning stop condition: if average Shaken applications rises above 7.0/match in `ecosystem_test.py 500 0`, disable the flag or raise the pressure threshold before proceeding.

---

## 8. AI Requirements

AI changes should be minimal and heuristic-only:

- Under `Stable Supply Lines`, AI may deploy/advance more aggressively due to extra order availability.
- Under `Dense Fog`, AI should slightly deprioritize low-damage ranged HQ attacks.
- With `Cavalry vs Shaken`, AI should prefer cavalry attacks into Shaken defenders when lethal or high value.
- With `Infantry + Artillery`, AI should not break a same-slot artillery setup without a clear tactical reason.

If implementation risk is high, AI awareness may be deferred after rule correctness tests, but balance results must be interpreted with that limitation.

---

## 9. Replay / Viewer Requirements

The replay viewer must explain the new mechanics without requiring raw log inspection.

Required display additions:

- Current battlefield situation name and one-line effect summary
- Situation change events in the timeline
- Commander reaction event cards
- Damage log annotations for situation/synergy modifiers
- Shaken-pressure note when a unit becomes Shaken under the reduced threshold

JSON keys must stay ASCII. Chinese labels render in HTML.

Suggested additive keys:

```json
"battlefield_situation": {...},
"commander_reaction": {...},
"damage_modifiers": [
  {"source": "situation", "id": "dense_fog", "delta": -1},
  {"source": "synergy", "id": "cavalry_pursuit", "delta": 1}
]
```

---

## 10. Balance And Tuning Knobs

### 10.1 Situation Knobs

- Situation start round: default 3
- Situation duration: default 3 full rounds
- Dense Fog ranged penalty: default -1, minimum damage 1
- Mud cavalry advance surcharge: +1 order
- Stable Supply Lines current-order bonus: +1 above `max_orders`, capped by global `MAX_ORDERS`

### 10.2 Commander Knobs

- Reaction once per match only
- Napoleon order gain: +1
- Blücher token: `后备国民军` 1/2 line infantry token
- Blücher fallback order gain: +1 if no rear slot exists
- Kutuzov heal: 1

### 10.3 Synergy Knobs

- Artillery synergy bonus: +1 unit damage only
- Cavalry pursuit bonus: +1 defender damage
- Skirmisher Hold is deferred from MVP

### 10.4 Shaken Pressure Knobs

- HQ pressure threshold: 7 HP
- Unit-loss pressure threshold: 2 units/full round
- Damage threshold while pressured: 1+

---

## 11. Test Requirements

Focused tests:

- Situation cycle is deterministic by seed and does not repeat before all 4 appear.
- Dense Fog reduces ranged damage but never below 1.
- Dense Fog does not override `闪避` reducing damage to 0.
- Mud makes cavalry advance cost +1 order.
- Cannon Smoke suppresses only first `齐射` attack per player action.
- Stable Supply Lines can create `current_orders = max_orders + 1` but never exceeds global `MAX_ORDERS`.
- Each commander reaction fires once and logs/export metadata.
- Blücher creates a token without duplicating a living discard-pile card.
- Infantry + artillery synergy affects only unit damage, not HQ damage.
- Cavalry vs Shaken applies +1 damage.
- Skirmisher Hold is not implemented in MVP.
- Shaken Pressure lowers damage threshold only when pressure condition is true.
- Existing Shaken recovery remains unchanged.
- Viewer/export contract includes new additive metadata without breaking old keys.
- Each layer can be enabled/disabled independently through its feature flag.

Balance checks:

```bash
python3 -m unittest test_rule_tuning.py
python3 -m unittest test_viewer_export_contract.py
python3 ecosystem_test.py 500 0
python3 ecosystem_test.py 500 500
```

Acceptance bands:

- PacingRisk <= 0.30
- Faction win rates roughly 45%-55%; investigate <43% or >57%
- Mirror first-player <= 65%
- Shaken frequency should not explode above the current accepted band without explicit retuning

---

## 12. Risks And Mitigations

| Risk | Mitigation |
|---|---|
| Situation effects feel random rather than strategic | Keep effects mild, public, deterministic, and long enough to plan around |
| Stable Supply Lines accelerates pacing too much | Tune to temporary order or move start round later |
| Commander reactions create faction imbalance | Each reaction is once per match and has fallback caps |
| Synergies create hidden math | Log every modifier and export `damage_modifiers` |
| Shaken becomes too common | Keep pressure derived, tune threshold, run ecosystem checks |
| AI underuses new rules | Add minimal heuristics or interpret balance as pre-AI-tuning |

---

## 13. Acceptance Criteria

- [ ] A match can run with battlefield situations enabled without changing deck size, HQ HP, or victory settlement.
- [ ] Situation changes are deterministic for a fixed seed.
- [ ] Every new modifier is represented in battle logs and exported replay metadata.
- [ ] Commander reactions fire at most once per match.
- [ ] Unit synergies are deterministic and visible in logs.
- [ ] Shaken Pressure uses existing `is_shaken` and does not add a hidden morale meter.
- [ ] Existing test suites pass.
- [ ] Each feature flag can be disabled without breaking baseline match simulation.
- [ ] Ecosystem balance remains within accepted gates or produces a clear tuning report.

---

## 14. Open Questions For Review

1. Should battlefield situations start at round 3 or round 1? Current recommendation: round 3 to let early deployment breathe.
2. Should Stable Supply Lines use current-order overcap or first-action discount? Current recommendation: current-order overcap, fallback to first-action discount if simpler.
3. Is Blücher's 1/2 `后备国民军` token sufficiently Prussian, or should it be 0/3 defensive? Current recommendation: 1/2 for simplicity.
4. Should Skirmisher Hold remain deferred, or be redesigned into a real gameplay rule for a later pack?
