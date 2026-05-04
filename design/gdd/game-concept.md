# Napoleon Card Tactics

**Status**: In Design  
**Owner**: Game Design  
**Last Updated**: 2026-05-05  

## Overview

Napoleon Card Tactics is a two-player tactical card game about Napoleonic battlefield pressure. Players command national decks, deploy infantry, cavalry, artillery, skirmishers, and guards across three battlefield lines, then spend orders to develop tempo, advance units, and break the enemy HQ.

The current project is engine-independent. The playable rules live in the Python simulator and HTML AI match viewer under `prototypes/card-battle-sim/`. The immediate goal is not engine production; it is validating whether the paper and browser prototype produces readable, interesting, and balanced matches.

## Player Fantasy

The player fantasy is being a Napoleonic field commander under constrained orders: forming lines, committing cavalry at the right moment, deciding when artillery should clear formations or threaten HQ, and accepting national tradeoffs. France should feel elite and aggressive, Prussia disciplined and resilient, and Russia attritional with costly long-game effects.

## Core Rules

The battlefield has three lines per player: rear, main, and skirmish. **All
UNIT cards deploy from hand to the rear line** (the rear-deploy-only rule). To
threaten the enemy HQ, a unit must be advanced rear→main→skirmish, costing 1
order per advance step. Skirmish slots are shared between players (a side that
already occupies slot N blocks the opponent from that slot).

A second card category, **event cards**, resolves immediately and does not
deploy to a line. Currently only Prussia has event cards (国防动员).

Each turn:

1. Draw 2 cards (hand limit 7).
2. Restore orders. Orders start at 1 on turn 1 and grow +1 each turn (cap 16).
3. Deploy UNIT cards into rear line / play EVENT cards.
4. Advance units rear→main and main→skirmish (each step costs 1 order).
5. Resolve attacks. Surviving "熔岩战术" attackers in main line return to rear.
6. Check HQ destruction or hard timeout at turn 30.

Active keywords:

- Universal: 冲锋 (charge), 结阵 (formation), 齐射 (volley), 远程 (ranged),
  闪避 (evade), 突破 (breakthrough — also bypasses 结阵 reduction), 守卫 (guard),
  侧翼迂回 (flank — cavalry can attack rear at range 3), 阿尔科莱精神
  (mobile artillery, +2 attack on reaching skirmish line)
- France-only: 军团联动 (corps synergy — same-slot friendly cavalry +1 attack
  when this artillery is in main/skirmish)
- Prussia-only: 死神威慑 (Death's Head intimidation — enemy in same slot
  -1 attack, multiple sources stack, min 0)
- Russia-only: 自残N (self-damage to own HQ on play), 光环+1攻 / 光环+1血
  (permanent stat aura applied on play to other friendlies), 熔岩战术
  (Cossack lava — main-line attacker returns to rear after attack), 焦土补给
  (scorched earth — owner's max_orders +1 next turn when this unit dies)
- EVENT cards: 国防动员 (Landwehr mobilisation — 2 orders, target one friendly
  INFANTRY for permanent +1/+2 and immediate +2 heal)

## Formulas

**Damage** (let A = attacker effective attack, D = defender base attack):

- Cavalry vs unformed infantry/guard: damage_to_defender = 2A
- Cavalry (no 突破) vs formed infantry/guard: damage_to_defender = max(1, A÷2)
- Cavalry with 突破 vs formed infantry/guard: damage_to_defender = A
  (breakthrough ignores formation reduction)
- Artillery vs formed infantry/guard: damage_to_defender = A + 2
- Artillery vs unformed infantry/guard: damage_to_defender = A + 1
- Otherwise: damage_to_defender = A
- Counter (damage_to_attacker):
  - Ranged artillery attacker: 0
  - Defender is artillery: D ÷ 2
  - Otherwise: D
- Skirmisher with 闪避: first non-artillery hit deals 0 (one-shot per match)
- 齐射: +1 pre-strike damage on this attacker's first attack of the turn

**Effective attack** (A) for an attacker with battlefield context:

  A = base_attack
      + 1 if attacker is cavalry AND a same-slot friendly artillery with
        军团联动 is in main/skirmish
      − N where N = number of enemy units in same slot with 死神威慑
      (clamped to ≥ 0)

**Order curve**:

- Turn 1: max_orders = 1
- Each subsequent turn: max_orders += 1, capped at 16
- 焦土补给 trigger: defender's max_orders += 1 immediately on its death
  (also capped at 16)
- Ranged-artillery HQ strike costs 1 extra order

**Draw**: 2 cards per turn start, hand limit 7. No fatigue on empty deck.

**HQ**: starts at 14 HP. Match ends when one HQ ≤ 0; if both HQs survive turn
30, higher remaining HP wins (tie possible).

**Example calculations**:

- 法 龙骑兵团 (3 atk) charges 普 普鲁士线列军 (4 atk, formed):
  damage_to_defender = max(1, 3÷2) = 1, damage_to_attacker = 4. Bad trade for
  France unless 军团联动 boost present.
- 法 胸甲骑兵 (6 atk, 突破) charges same target:
  damage_to_defender = 6 (突破 bypasses formation), damage_to_attacker = 4.
  Cuirassiers kill in one strike.
- 法 12磅野战炮 (4 atk, ranged) shells 普 普鲁士线列军:
  damage_to_defender = 4 + 2 = 6 (formation bonus), damage_to_attacker = 0.

## Edge Cases

- A player with an empty deck draws nothing and does not take fatigue damage.
- A full deployment line prevents additional deployment to that line.
- A unit deployed this turn cannot act unless it has charge.
- Ranged artillery can attack HQ only when enemy skirmish and main lines are empty, and it spends 1 extra order for the HQ strike.
- Aura effects currently modify card instances on existing battlefield units. Viewer logs must make these effects understandable because the effect is otherwise easy to miss.
- Event cards (国防动员): if no friendly INFANTRY is on the battlefield, the
  card cannot be played; it stays in hand and orders are not spent.
- 熔岩战术: triggers only when attacking from MAIN line and attacker survives
  counter. Skirmish-line attackers do NOT return (they're "stuck in the front").
  If REAR is full, return fails silently and unit stays in main.
- 焦土补给: triggers on death from any source (combat counter or skirmish
  trade). Same-turn multiple deaths each grant +1, all capped at MAX_ORDERS=16.
- 军团联动 / 死神威慑 are computed from live battlefield state, not snapshots.
  Killing the source unit removes the aura immediately.

## Dependencies

- Current simulation code: `prototypes/card-battle-sim/game.py`, `combat.py`, `ai.py`, `cards.py`, `game_state.py`.
- Earlier simulator: `prototypes/rule-simulator/`.
- Current viewer: `prototypes/card-battle-sim/viewer.html`.
- Current replay data: `prototypes/card-battle-sim/match_*.json`.
- Printable prototype: `prototypes/card-battle-sim/napoleon_cards.pdf`.
- Research basis: `design/research/napoleon/`.

## Tuning Knobs

- HQ starting HP (currently 14, safe range 10–20).
- Starting hand size (currently 4) and second-player compensation (currently +1 draw).
- Per-turn draw count (currently 2) and hand limit (currently 7).
- Order growth per turn (currently +1) and maximum orders (currently 16).
- Hard timeout MAX_TURNS (currently 30).
- Ranged artillery HQ strike cost (currently +1 order).
- Line capacity (currently 4 slots).
- Card counts and faction-specific stat lines.
- AI deployment, advance, and target-priority heuristics.
- Event card cost (currently 国防动员 = 2).
- 焦土补给 max_orders gain per trigger (currently +1, capped at MAX_ORDERS).
- 死神威慑 zone (currently same slot only).
- 军团联动 zone (currently same slot, artillery in MAIN/SKIRMISH only).
- 突破 effect — currently both overflow-to-HQ and bypass-formation.

## Acceptance Criteria

- The simulator can export a replay JSON without errors.
- The viewer can load `viewer.html` and `match_data.json` through a local HTTP server.
- Core rule changes have focused regression tests.
- A typical AI match ends without timeout and remains readable in the viewer.
- Human playtest notes can identify whether hand size, order pressure, and line control feel understandable.
