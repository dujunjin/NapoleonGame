# v0.3A Command Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add v0.3A Command Layer: one default commander per faction, five shared Tactical Objectives, deterministic assignment, replay/export metadata, and viewer visibility while preserving v0.2 balance gates.

**Architecture:** Add small data models for commanders and objectives without changing deck size or card pools. Store per-player command state on `Player`, resolve commander/objective effects inside the existing turn loop, export metadata through `export_match.py`, and render it in the existing HTML replay panels. Keep this as a vertical slice: no campaign, no deckbuilding, no fourth faction, no commander progression.

**Tech Stack:** Python dataclasses/enums, `unittest`, deterministic simulator, JSON replay export, vanilla HTML/CSS/JS viewer.

---

## Source Spec

Use this product design as the source of truth:

- `docs/superpowers/specs/2026-05-06-v03a-command-layer-product-design.md`

Current accepted v0.2 baseline:

- `python3 ecosystem_test.py 500 0`: France 48.4%, Prussia 52.4%, Russia 49.2%, PacingRisk 0.188.
- `python3 ecosystem_test.py 500 500`: France 47.1%, Prussia 53.3%, Russia 49.5%, PacingRisk 0.180.
- `python3 -m unittest test_rule_tuning.py`: 42 tests passing.

## Acceptance Gates

Functional:

- Unit tests pass.
- Each faction gets exactly one default commander.
- Commander can be used once and cannot be used twice.
- Each player gets exactly one deterministic public Tactical Objective.
- P1 and P2 do not receive the same objective when five objectives are available.
- Objectives complete at most once.
- Objective reward applies at most once.
- Replay export includes commander/objective metadata.
- Viewer shows commander and objective state.

Balance:

- `python3 ecosystem_test.py 500 0`:
  - All faction overall rates 45%-55%.
  - All mirror first-player <=65%.
  - France first-player vs Russia <=65%.
  - PacingRisk <=0.30.
  - No matchup average >21 turns.
- `python3 ecosystem_test.py 500 500` confirms the same.

Objective quality:

- Each objective completion rate is 30%-75%.
- At least 3 of 5 objectives complete in 35%-65% of games.
- No objective correlates with any faction exceeding 55% overall.

## File Structure

Create:

- `prototypes/card-battle-sim/commanders.py`
  - Commander definitions and default commander lookup.

- `prototypes/card-battle-sim/objectives.py`
  - Tactical Objective definitions, deterministic assignment, state helpers, and trigger checks.

Modify:

- `prototypes/card-battle-sim/game_state.py`
  - Add commander/objective runtime fields to `Player`.

- `prototypes/card-battle-sim/game.py`
  - Initialize commander/objective state.
  - Apply commander effects.
  - Track objective triggers and rewards.
  - Extend `GameResult` with objective completion counters if useful for ecosystem metrics.

- `prototypes/card-battle-sim/ai.py`
  - Add minimal commander-use decisions.
  - Add minimal objective pursuit nudges.

- `prototypes/card-battle-sim/export_match.py`
  - Include commander/objective metadata in snapshots and match meta.
  - Ensure exported replay uses the same command-layer logic as `game.py`.

- `prototypes/card-battle-sim/viewer.html`
  - Show commander and objective state.
  - Show action summaries for commander use and objective completion.

- `prototypes/card-battle-sim/ecosystem_test.py`
  - Track objective completion rates.

- `prototypes/card-battle-sim/test_rule_tuning.py`
  - Add functional tests for commanders, objective assignment, objective completion, and export metadata.

- `prototypes/card-battle-sim/README.md`
  - Update v0.3A baseline after acceptance.

- `AGENTS.md`
  - Update current project memory after acceptance.

Do not modify:

- HQ HP.
- Deck size.
- Existing card pool.
- Operational Pressure start turn.
- Breakthrough Reward base rule.
- Max turns.
- v0.4 faction design.

## Task 1: Add Commander Data Model

**Files:**

- Create: `prototypes/card-battle-sim/commanders.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Add failing commander definition test**

In `prototypes/card-battle-sim/test_rule_tuning.py`, add imports:

```python
from commanders import COMMANDERS, DEFAULT_COMMANDERS, CommanderId, get_default_commander
```

Add this test after `test_global_constants_pinned`:

```python
    def test_default_commanders_exist_for_all_factions(self):
        self.assertEqual(DEFAULT_COMMANDERS, {
            Faction.FRANCE: CommanderId.NAPOLEON,
            Faction.PRUSSIA: CommanderId.BLUCHER,
            Faction.RUSSIA: CommanderId.KUTUZOV,
        })

        self.assertEqual(get_default_commander(Faction.FRANCE).name, "拿破仑")
        self.assertEqual(get_default_commander(Faction.PRUSSIA).name, "布吕歇尔")
        self.assertEqual(get_default_commander(Faction.RUSSIA).name, "库图佐夫")

        for commander in COMMANDERS.values():
            self.assertFalse(commander.enters_deck)
            self.assertEqual(commander.uses_per_match, 1)
```

- [ ] **Step 2: Run test and confirm it fails**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_default_commanders_exist_for_all_factions
```

Expected:

- Import fails because `commanders.py` does not exist.

- [ ] **Step 3: Create `commanders.py`**

Create `prototypes/card-battle-sim/commanders.py`:

```python
"""Commander definitions for v0.3A command layer."""

from dataclasses import dataclass
from enum import Enum
from cards import Faction


class CommanderId(Enum):
    NAPOLEON = "napoleon"
    BLUCHER = "blucher"
    KUTUZOV = "kutuzov"


@dataclass(frozen=True)
class Commander:
    id: CommanderId
    name: str
    faction: Faction
    ability_name: str
    description: str
    uses_per_match: int = 1
    enters_deck: bool = False


COMMANDERS = {
    CommanderId.NAPOLEON: Commander(
        id=CommanderId.NAPOLEON,
        name="拿破仑",
        faction=Faction.FRANCE,
        ability_name="Imperial Breakthrough",
        description="本回合一条友方战线的首次 HQ 直击 +1。",
    ),
    CommanderId.BLUCHER: Commander(
        id=CommanderId.BLUCHER,
        name="布吕歇尔",
        faction=Faction.PRUSSIA,
        ability_name="Counterstroke",
        description="本回合受伤友军攻击 +1。",
    ),
    CommanderId.KUTUZOV: Commander(
        id=CommanderId.KUTUZOV,
        name="库图佐夫",
        faction=Faction.RUSSIA,
        ability_name="Strategic Withdrawal",
        description="撤回一个非后方线友军，治疗 1，并恢复 HQ 1。",
    ),
}


DEFAULT_COMMANDERS = {
    Faction.FRANCE: CommanderId.NAPOLEON,
    Faction.PRUSSIA: CommanderId.BLUCHER,
    Faction.RUSSIA: CommanderId.KUTUZOV,
}


def get_default_commander(faction: Faction) -> Commander:
    return COMMANDERS[DEFAULT_COMMANDERS[faction]]
```

- [ ] **Step 4: Run commander definition test**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_default_commanders_exist_for_all_factions
```

Expected:

- Test passes.

- [ ] **Step 5: Run full tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py
```

Expected:

- All tests pass.

- [ ] **Step 6: Commit commander definitions**

Run:

```bash
git add prototypes/card-battle-sim/commanders.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat: add default commanders"
```

## Task 2: Add Tactical Objective Data Model

**Files:**

- Create: `prototypes/card-battle-sim/objectives.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Add failing objective assignment test**

In `test_rule_tuning.py`, add imports:

```python
from objectives import ObjectiveId, OBJECTIVES, assign_objectives
```

Add this test after the commander definition test:

```python
    def test_tactical_objectives_are_deterministic_and_distinct(self):
        p1_obj, p2_obj = assign_objectives(seed=42)
        p1_obj_again, p2_obj_again = assign_objectives(seed=42)

        self.assertEqual((p1_obj.id, p2_obj.id), (p1_obj_again.id, p2_obj_again.id))
        self.assertNotEqual(p1_obj.id, p2_obj.id)
        self.assertEqual(len(OBJECTIVES), 5)
        self.assertIn(ObjectiveId.SEIZE_SKIRMISH, OBJECTIVES)
        self.assertIn(ObjectiveId.FIRST_BLOOD_HQ, OBJECTIVES)
        self.assertIn(ObjectiveId.HOLD_MAIN, OBJECTIVES)
        self.assertIn(ObjectiveId.PREPARE_GUNS, OBJECTIVES)
        self.assertIn(ObjectiveId.SACRIFICE_FOR_TIME, OBJECTIVES)
```

- [ ] **Step 2: Run test and confirm it fails**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_tactical_objectives_are_deterministic_and_distinct
```

Expected:

- Import fails because `objectives.py` does not exist.

- [ ] **Step 3: Create `objectives.py`**

Create `prototypes/card-battle-sim/objectives.py`:

```python
"""Tactical Objective definitions for v0.3A command layer."""

import random
from dataclasses import dataclass
from enum import Enum


class ObjectiveId(Enum):
    SEIZE_SKIRMISH = "seize_skirmish"
    FIRST_BLOOD_HQ = "first_blood_hq"
    HOLD_MAIN = "hold_main"
    PREPARE_GUNS = "prepare_guns"
    SACRIFICE_FOR_TIME = "sacrifice_for_time"


@dataclass(frozen=True)
class TacticalObjective:
    id: ObjectiveId
    name: str
    description: str
    reward_text: str


OBJECTIVES = {
    ObjectiveId.SEIZE_SKIRMISH: TacticalObjective(
        ObjectiveId.SEIZE_SKIRMISH,
        "夺取散兵线",
        "行动结束时，己方散兵线有单位且敌方散兵线无单位。",
        "抽 1 张牌。",
    ),
    ObjectiveId.FIRST_BLOOD_HQ: TacticalObjective(
        ObjectiveId.FIRST_BLOOD_HQ,
        "压迫 HQ",
        "首次对敌方 HQ 造成伤害。",
        "本回合 current_orders +1，不超过 max_orders。",
    ),
    ObjectiveId.HOLD_MAIN: TacticalObjective(
        ObjectiveId.HOLD_MAIN,
        "稳住主线",
        "完整轮结束时，己方主力线至少有 2 个单位。",
        "HQ 恢复 1。",
    ),
    ObjectiveId.PREPARE_GUNS: TacticalObjective(
        ObjectiveId.PREPARE_GUNS,
        "炮兵准备",
        "一个友方炮兵在后方线开始并结束己方行动。",
        "下一次炮兵攻击 +1。",
    ),
    ObjectiveId.SACRIFICE_FOR_TIME: TacticalObjective(
        ObjectiveId.SACRIFICE_FOR_TIME,
        "牺牲换时间",
        "完整轮内己方至少 1 个单位死亡，且敌方没有造成 HQ 伤害。",
        "抽 1 张牌。",
    ),
}


def assign_objectives(seed: int) -> tuple[TacticalObjective, TacticalObjective]:
    rng = random.Random(seed + 31003)
    ids = list(OBJECTIVES.keys())
    p1_id = rng.choice(ids)
    remaining = [objective_id for objective_id in ids if objective_id != p1_id]
    p2_id = rng.choice(remaining)
    return OBJECTIVES[p1_id], OBJECTIVES[p2_id]
```

- [ ] **Step 4: Run objective assignment test**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_tactical_objectives_are_deterministic_and_distinct
```

Expected:

- Test passes.

- [ ] **Step 5: Run full tests and commit**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py
git add prototypes/card-battle-sim/objectives.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat: add tactical objective definitions"
```

Expected:

- All tests pass before commit.

## Task 3: Add Player Command Runtime State

**Files:**

- Modify: `prototypes/card-battle-sim/game_state.py`
- Modify: `prototypes/card-battle-sim/game.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Add failing player initialization test**

Add this test after objective assignment test:

```python
    def test_new_players_receive_commander_and_objective_state(self):
        result = play_one_game(Faction.FRANCE, Faction.RUSSIA, seed=42)

        self.assertIsNotNone(result.p1_commander)
        self.assertIsNotNone(result.p2_commander)
        self.assertIsNotNone(result.p1_objective)
        self.assertIsNotNone(result.p2_objective)
        self.assertEqual(result.p1_commander, "拿破仑")
        self.assertEqual(result.p2_commander, "库图佐夫")
        self.assertNotEqual(result.p1_objective, result.p2_objective)
```

- [ ] **Step 2: Run test and confirm it fails**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_new_players_receive_commander_and_objective_state
```

Expected:

- Test fails because `GameResult` has no commander/objective fields.

- [ ] **Step 3: Add fields to `Player`**

In `game_state.py`, add these fields to `Player`:

```python
    commander_id: Optional[str] = None
    commander_name: Optional[str] = None
    commander_used: bool = False
    commander_use_turn: int = 0
    commander_active_line: Optional[Line] = None
    objective_id: Optional[str] = None
    objective_name: Optional[str] = None
    objective_completed: bool = False
    objective_completed_turn: int = 0
    objective_reward_pending: Optional[str] = None
    objective_stats: dict = field(default_factory=dict)
```

- [ ] **Step 4: Extend `GameResult`**

In `game.py`, add fields to `GameResult`:

```python
    p1_commander: str = ""
    p2_commander: str = ""
    p1_objective: str = ""
    p2_objective: str = ""
    p1_objective_completed: bool = False
    p2_objective_completed: bool = False
```

- [ ] **Step 5: Add initialization helper in `game.py`**

Import:

```python
from commanders import get_default_commander
from objectives import assign_objectives
```

Add helper before `play_one_game`:

```python
def initialize_command_layer(p1: Player, p2: Player, seed: int) -> None:
    p1_commander = get_default_commander(p1.faction)
    p2_commander = get_default_commander(p2.faction)
    p1.commander_id = p1_commander.id.value
    p1.commander_name = p1_commander.name
    p2.commander_id = p2_commander.id.value
    p2.commander_name = p2_commander.name

    p1_objective, p2_objective = assign_objectives(seed)
    p1.objective_id = p1_objective.id.value
    p1.objective_name = p1_objective.name
    p2.objective_id = p2_objective.id.value
    p2.objective_name = p2_objective.name
```

- [ ] **Step 6: Call initialization in `play_one_game`**

After `battlefield = Battlefield()` in `play_one_game`, add:

```python
    initialize_command_layer(p1, p2, seed)
```

- [ ] **Step 7: Add command data to every `GameResult` return**

For every `return GameResult(...)` in `play_one_game`, add:

```python
                              p1_commander=p1.commander_name or "",
                              p2_commander=p2.commander_name or "",
                              p1_objective=p1.objective_name or "",
                              p2_objective=p2.objective_name or "",
                              p1_objective_completed=p1.objective_completed,
                              p2_objective_completed=p2.objective_completed,
```

- [ ] **Step 8: Run focused and full tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_new_players_receive_commander_and_objective_state
python3 -m unittest test_rule_tuning.py
```

Expected:

- Focused test passes.
- Full suite passes.

- [ ] **Step 9: Commit runtime state**

Run:

```bash
git add prototypes/card-battle-sim/game_state.py prototypes/card-battle-sim/game.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat: initialize command layer state"
```

## Task 4: Implement Commander Abilities

**Files:**

- Modify: `prototypes/card-battle-sim/game.py`
- Modify: `prototypes/card-battle-sim/ai.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Add failing tests for commander usage**

Add these tests after command-layer initialization test:

```python
    def test_napoleon_commander_marks_line_for_hq_bonus_once(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    commander_id="napoleon", commander_name="拿破仑")
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        bf = Battlefield()
        unit = BattleUnit(card=self.make_card("帝国步兵团", attack=4), current_hp=4,
                          current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        bf.p1_main = [unit]
        log = []

        self.assertTrue(use_commander_ability(p1, p2, bf, 0, turn=5, log=log))
        self.assertTrue(p1.commander_used)
        self.assertEqual(p1.commander_active_line, Line.MAIN)
        self.assertFalse(use_commander_ability(p1, p2, bf, 0, turn=5, log=log))

    def test_blucher_commander_buffs_wounded_units_once(self):
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=14,
                    commander_id="blucher", commander_name="布吕歇尔")
        p2 = Player(name="P2", faction=Faction.FRANCE, hq_hp=14)
        bf = Battlefield()
        wounded = BattleUnit(card=self.make_card("普鲁士线列军", attack=4, health=4),
                             current_hp=2, current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        healthy = BattleUnit(card=self.make_card("西里西亚国民军", attack=2, health=3),
                             current_hp=3, current_line=Line.MAIN, slot=2, deployed_this_turn=False)
        bf.p1_main = [wounded, healthy]

        self.assertTrue(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))
        self.assertEqual(wounded.card.attack, 5)
        self.assertEqual(healthy.card.attack, 2)
        self.assertFalse(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))

    def test_kutuzov_commander_retreats_unit_heals_unit_and_hq_once(self):
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=10,
                    commander_id="kutuzov", commander_name="库图佐夫")
        p2 = Player(name="P2", faction=Faction.FRANCE, hq_hp=14)
        bf = Battlefield()
        unit = BattleUnit(card=self.make_card("俄国线列军", health=5),
                          current_hp=3, current_line=Line.SKIRMISH, slot=1,
                          deployed_this_turn=False)
        bf.p1_skirmish = [unit]

        self.assertTrue(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))
        self.assertEqual(unit.current_line, Line.REAR)
        self.assertEqual(unit.current_hp, 4)
        self.assertEqual(p1.hq_hp, 11)
        self.assertIn(unit, bf.p1_rear)
        self.assertFalse(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))
```

Add import:

```python
from game import use_commander_ability
```

Fold it into the existing multi-line `from game import (...)` import.

- [ ] **Step 2: Run commander tests and confirm they fail**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest \
  test_rule_tuning.RuleTuningTests.test_napoleon_commander_marks_line_for_hq_bonus_once \
  test_rule_tuning.RuleTuningTests.test_blucher_commander_buffs_wounded_units_once \
  test_rule_tuning.RuleTuningTests.test_kutuzov_commander_retreats_unit_heals_unit_and_hq_once
```

Expected:

- Import fails because `use_commander_ability` does not exist.

- [ ] **Step 3: Implement `use_commander_ability` in `game.py`**

Add this helper before `play_turn`:

```python
def use_commander_ability(player: Player, opponent: Player, battlefield: Battlefield,
                          player_idx: int, turn: int, log: Optional[List[str]] = None) -> bool:
    if player.commander_used or not player.commander_id:
        return False

    units = battlefield.all_units(player_idx)

    if player.commander_id == "napoleon":
        candidates = [u for u in units if not u.is_dead]
        if not candidates:
            return False
        chosen = max(candidates, key=lambda u: u.card.attack)
        player.commander_active_line = chosen.current_line
        player.commander_used = True
        player.commander_use_turn = turn
        if log is not None:
            log.append(f"  ★ {player.name} 使用指挥官【拿破仑】→ {chosen.current_line.value} 首次 HQ 直击 +1")
        return True

    if player.commander_id == "blucher":
        wounded = [u for u in units if not u.is_dead and u.current_hp < u.card.health]
        if not wounded:
            return False
        for unit in wounded:
            unit.card = _apply_aura(unit.card, attack_bonus=1)
        player.commander_used = True
        player.commander_use_turn = turn
        if log is not None:
            log.append(f"  ★ {player.name} 使用指挥官【布吕歇尔】→ {len(wounded)} 个受伤友军 +1 攻")
        return True

    if player.commander_id == "kutuzov":
        candidates = [u for u in units if not u.is_dead and u.current_line != Line.REAR]
        if not candidates:
            return False
        chosen = min(candidates, key=lambda u: (u.current_hp, -u.card.cost))
        battlefield.get_line(player_idx, chosen.current_line).remove(chosen)
        chosen.current_line = Line.REAR
        chosen.current_hp = min(chosen.card.health, chosen.current_hp + 1)
        chosen.has_acted_this_turn = True
        battlefield.get_line(player_idx, Line.REAR).append(chosen)
        battlefield.sort_line(player_idx, Line.REAR)
        player.hq_hp += 1
        player.commander_used = True
        player.commander_use_turn = turn
        if log is not None:
            log.append(f"  ★ {player.name} 使用指挥官【库图佐夫】→ {chosen.card.name} 撤回后方线，单位 +1 HP，HQ +1")
        return True

    return False
```

- [ ] **Step 4: Add AI commander use in `play_turn`**

In `play_turn`, after max orders/current orders are set for the turn and before attacks, call:

```python
    use_commander_ability(player, opponent, battlefield, player_idx, turn_num, log)
```

If this creates too much early commander use, move the call to immediately before `ai_attack_phase`.

- [ ] **Step 5: Apply Napoleon HQ bonus in attack flow**

Find HQ direct damage handling in `ai_attack_phase` in `ai.py`. Add support for `player.commander_active_line`:

```python
                commander_bonus = 0
                if getattr(active, "commander_active_line", None) == attacker.current_line:
                    commander_bonus = 1
                    active.commander_active_line = None
                dmg += commander_bonus
```

When writing attack event metadata, include:

```python
"commander_bonus": commander_bonus,
```

When logging, append ` +指挥官` if `commander_bonus > 0`.

- [ ] **Step 6: Run commander tests and full tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest \
  test_rule_tuning.RuleTuningTests.test_napoleon_commander_marks_line_for_hq_bonus_once \
  test_rule_tuning.RuleTuningTests.test_blucher_commander_buffs_wounded_units_once \
  test_rule_tuning.RuleTuningTests.test_kutuzov_commander_retreats_unit_heals_unit_and_hq_once
python3 -m unittest test_rule_tuning.py
```

Expected:

- Commander tests pass.
- Full suite passes.

- [ ] **Step 7: Commit commander behavior**

Run:

```bash
git add prototypes/card-battle-sim/game.py prototypes/card-battle-sim/ai.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat: add commander abilities"
```

## Task 5: Implement Objective Completion And Rewards

**Files:**

- Modify: `prototypes/card-battle-sim/objectives.py`
- Modify: `prototypes/card-battle-sim/game.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Add failing objective reward tests**

Add imports:

```python
from objectives import complete_objective
```

Add these tests after commander tests:

```python
    def test_first_blood_objective_completes_once_and_grants_order(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    objective_id="first_blood_hq", objective_name="压迫 HQ",
                    max_orders=3, current_orders=1)
        completed = complete_objective(p1, ObjectiveId.FIRST_BLOOD_HQ, turn=2, log=[])

        self.assertTrue(completed)
        self.assertTrue(p1.objective_completed)
        self.assertEqual(p1.current_orders, 2)
        self.assertFalse(complete_objective(p1, ObjectiveId.FIRST_BLOOD_HQ, turn=2, log=[]))

    def test_seize_skirmish_objective_draws_once(self):
        draw_card = self.make_card("援军")
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    deck=[draw_card], objective_id="seize_skirmish",
                    objective_name="夺取散兵线")
        completed = complete_objective(p1, ObjectiveId.SEIZE_SKIRMISH, turn=2, log=[])

        self.assertTrue(completed)
        self.assertIn(draw_card, p1.hand)
        self.assertEqual(len(p1.deck), 0)

    def test_hold_main_objective_heals_hq_once(self):
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=10,
                    objective_id="hold_main", objective_name="稳住主线")
        self.assertTrue(complete_objective(p1, ObjectiveId.HOLD_MAIN, turn=2, log=[]))
        self.assertEqual(p1.hq_hp, 11)

    def test_prepare_guns_sets_pending_artillery_bonus(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    objective_id="prepare_guns", objective_name="炮兵准备")
        self.assertTrue(complete_objective(p1, ObjectiveId.PREPARE_GUNS, turn=2, log=[]))
        self.assertEqual(p1.objective_reward_pending, "artillery_attack_plus_1")

    def test_sacrifice_for_time_objective_draws_once(self):
        draw_card = self.make_card("援军")
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=14,
                    deck=[draw_card], objective_id="sacrifice_for_time",
                    objective_name="牺牲换时间")
        self.assertTrue(complete_objective(p1, ObjectiveId.SACRIFICE_FOR_TIME, turn=2, log=[]))
        self.assertIn(draw_card, p1.hand)
```

- [ ] **Step 2: Run objective reward tests and confirm they fail**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest \
  test_rule_tuning.RuleTuningTests.test_first_blood_objective_completes_once_and_grants_order \
  test_rule_tuning.RuleTuningTests.test_seize_skirmish_objective_draws_once \
  test_rule_tuning.RuleTuningTests.test_hold_main_objective_heals_hq_once \
  test_rule_tuning.RuleTuningTests.test_prepare_guns_sets_pending_artillery_bonus \
  test_rule_tuning.RuleTuningTests.test_sacrifice_for_time_objective_draws_once
```

Expected:

- Import fails because `complete_objective` does not exist.

- [ ] **Step 3: Implement `complete_objective`**

In `objectives.py`, add:

```python
def complete_objective(player, objective_id: ObjectiveId, turn: int, log=None) -> bool:
    if player.objective_completed:
        return False
    if player.objective_id != objective_id.value:
        return False

    player.objective_completed = True
    player.objective_completed_turn = turn

    if objective_id == ObjectiveId.SEIZE_SKIRMISH:
        player.draw(1)
        reward = "抽 1 张牌"
    elif objective_id == ObjectiveId.FIRST_BLOOD_HQ:
        player.current_orders = min(player.max_orders, player.current_orders + 1)
        reward = "current_orders +1"
    elif objective_id == ObjectiveId.HOLD_MAIN:
        player.hq_hp += 1
        reward = "HQ +1"
    elif objective_id == ObjectiveId.PREPARE_GUNS:
        player.objective_reward_pending = "artillery_attack_plus_1"
        reward = "下一次炮兵攻击 +1"
    elif objective_id == ObjectiveId.SACRIFICE_FOR_TIME:
        player.draw(1)
        reward = "抽 1 张牌"
    else:
        return False

    if log is not None:
        log.append(f"  🎯 战术目标完成【{player.objective_name}】→ {reward}")
    return True
```

- [ ] **Step 4: Add trigger helper in `game.py`**

Import:

```python
from objectives import ObjectiveId, complete_objective
```

Add helper before `play_one_game`:

```python
def check_action_objectives(player: Player, opponent: Player, battlefield: Battlefield,
                            player_idx: int, turn: int, dealt_hq_damage: bool,
                            log: Optional[List[str]] = None) -> None:
    if player.objective_completed or not player.objective_id:
        return

    if player.objective_id == ObjectiveId.SEIZE_SKIRMISH.value:
        if battlefield.get_line(player_idx, Line.SKIRMISH) and not battlefield.get_line(1 - player_idx, Line.SKIRMISH):
            complete_objective(player, ObjectiveId.SEIZE_SKIRMISH, turn, log)
    elif player.objective_id == ObjectiveId.FIRST_BLOOD_HQ.value and dealt_hq_damage:
        complete_objective(player, ObjectiveId.FIRST_BLOOD_HQ, turn, log)
    elif player.objective_id == ObjectiveId.PREPARE_GUNS.value:
        rear_units = battlefield.get_line(player_idx, Line.REAR)
        if any(unit.card.unit_type == UnitType.ARTILLERY for unit in rear_units):
            complete_objective(player, ObjectiveId.PREPARE_GUNS, turn, log)


def check_round_objectives(p1: Player, p2: Player, battlefield: Battlefield,
                           turn: int,
                           p1_dealt_hq_damage: bool,
                           p2_dealt_hq_damage: bool,
                           p1_unit_died: bool,
                           p2_unit_died: bool,
                           log: Optional[List[str]] = None) -> None:
    if p1.objective_id == ObjectiveId.HOLD_MAIN.value and len(battlefield.p1_main) >= 2:
        complete_objective(p1, ObjectiveId.HOLD_MAIN, turn, log)
    if p2.objective_id == ObjectiveId.HOLD_MAIN.value and len(battlefield.p2_main) >= 2:
        complete_objective(p2, ObjectiveId.HOLD_MAIN, turn, log)

    if p1.objective_id == ObjectiveId.SACRIFICE_FOR_TIME.value and p1_unit_died and not p2_dealt_hq_damage:
        complete_objective(p1, ObjectiveId.SACRIFICE_FOR_TIME, turn, log)
    if p2.objective_id == ObjectiveId.SACRIFICE_FOR_TIME.value and p2_unit_died and not p1_dealt_hq_damage:
        complete_objective(p2, ObjectiveId.SACRIFICE_FOR_TIME, turn, log)
```

- [ ] **Step 5: Call objective checks in `play_one_game`**

Before each `play_turn`, record unit counts:

```python
        p1_units_before = len(battlefield.all_units(0))
        p2_units_before = len(battlefield.all_units(1))
```

After each `play_turn`, compute:

```python
        p1_unit_died_this_action = len(battlefield.all_units(0)) < p1_units_before
        p2_unit_died_this_action = len(battlefield.all_units(1)) < p2_units_before
```

After P1 action, call:

```python
        check_action_objectives(p1, p2, battlefield, 0, turn, p1_dealt_hq_damage, log)
```

After P2 action, call:

```python
        check_action_objectives(p2, p1, battlefield, 1, turn, p2_dealt_hq_damage, log)
```

Before Operational Pressure, call:

```python
        check_round_objectives(
            p1, p2, battlefield, turn,
            p1_dealt_hq_damage=p1_dealt_hq_damage,
            p2_dealt_hq_damage=p2_dealt_hq_damage,
            p1_unit_died=p1_unit_died_this_round,
            p2_unit_died=p2_unit_died_this_round,
            log=log,
        )
```

Use booleans accumulated across both actions:

```python
        p1_unit_died_this_round = False
        p2_unit_died_this_round = False
```

at the start of each turn loop.

- [ ] **Step 6: Apply Prepare The Guns artillery bonus**

In `ai_attack_phase`, when an artillery unit attacks, add:

```python
            objective_bonus = 0
            if (attacker.card.unit_type == UnitType.ARTILLERY
                    and getattr(active, "objective_reward_pending", None) == "artillery_attack_plus_1"):
                objective_bonus = 1
                active.objective_reward_pending = None
```

Add `objective_bonus` to damage and attack metadata. Log ` +目标奖励` when used.

- [ ] **Step 7: Run objective reward tests and full tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest \
  test_rule_tuning.RuleTuningTests.test_first_blood_objective_completes_once_and_grants_order \
  test_rule_tuning.RuleTuningTests.test_seize_skirmish_objective_draws_once \
  test_rule_tuning.RuleTuningTests.test_hold_main_objective_heals_hq_once \
  test_rule_tuning.RuleTuningTests.test_prepare_guns_sets_pending_artillery_bonus \
  test_rule_tuning.RuleTuningTests.test_sacrifice_for_time_objective_draws_once
python3 -m unittest test_rule_tuning.py
```

Expected:

- Focused tests pass.
- Full suite passes.

- [ ] **Step 8: Commit objective behavior**

Run:

```bash
git add prototypes/card-battle-sim/objectives.py prototypes/card-battle-sim/game.py prototypes/card-battle-sim/ai.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat: add tactical objective rewards"
```

## Task 6: Add Export Metadata

**Files:**

- Modify: `prototypes/card-battle-sim/export_match.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Add failing export metadata test**

Add this test near existing export tests:

```python
    def test_export_includes_commander_and_objective_metadata(self):
        data = play_and_export(Faction.FRANCE, Faction.RUSSIA, seed=42)

        self.assertEqual(data["meta"]["p1_commander"], "拿破仑")
        self.assertEqual(data["meta"]["p2_commander"], "库图佐夫")
        self.assertIn("p1_objective", data["meta"])
        self.assertIn("p2_objective", data["meta"])
        self.assertIn("commander", data["timeline"][0]["state"]["p1"])
        self.assertIn("objective", data["timeline"][0]["state"]["p1"])
```

- [ ] **Step 2: Run test and confirm it fails**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_export_includes_commander_and_objective_metadata
```

Expected:

- Test fails because export metadata is missing.

- [ ] **Step 3: Initialize command layer in export**

In `export_match.py`, import:

```python
from game import initialize_command_layer, apply_operational_pressure
```

After `battlefield = Battlefield()`, add:

```python
    initialize_command_layer(p1, p2, seed)
```

- [ ] **Step 4: Add command fields to snapshots**

In `snapshot_battlefield`, under each player dict, add:

```python
            "commander": {
                "id": p1.commander_id,
                "name": p1.commander_name,
                "used": p1.commander_used,
                "use_turn": p1.commander_use_turn,
            },
            "objective": {
                "id": p1.objective_id,
                "name": p1.objective_name,
                "completed": p1.objective_completed,
                "completed_turn": p1.objective_completed_turn,
                "reward_pending": p1.objective_reward_pending,
            },
```

Use `p2` fields for the P2 block.

- [ ] **Step 5: Add command fields to meta**

In the returned `meta`, add:

```python
            "p1_commander": p1.commander_name,
            "p2_commander": p2.commander_name,
            "p1_objective": p1.objective_name,
            "p2_objective": p2.objective_name,
            "p1_objective_completed": p1.objective_completed,
            "p2_objective_completed": p2.objective_completed,
```

- [ ] **Step 6: Align export loop with command/objective logic**

Ensure `play_and_export` uses the same command/objective checks as `play_one_game`. Import and call:

```python
from game import check_action_objectives, check_round_objectives
```

after each player action and before pressure, using the same pattern from Task 5.

If this step is too large, at minimum ensure commander/objective initialization and snapshots are correct, then add a known limitation note to the final report. Do not claim objective timeline parity unless implemented.

- [ ] **Step 7: Run export metadata test and full tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.RuleTuningTests.test_export_includes_commander_and_objective_metadata
python3 -m unittest test_rule_tuning.py
```

Expected:

- Export metadata test passes.
- Full suite passes.

- [ ] **Step 8: Commit export metadata**

Run:

```bash
git add prototypes/card-battle-sim/export_match.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat: export command layer metadata"
```

## Task 7: Update Viewer Display

**Files:**

- Modify: `prototypes/card-battle-sim/viewer.html`

- [ ] **Step 1: Add visible command layer fields**

In the player info/header render function, show:

```text
Commander: <name> · unused/used
Objective: <name> · active/completed
```

Use existing panel styling. Do not redesign the whole viewer.

- [ ] **Step 2: Add action summary handling**

In the action summary/log derivation code, detect log lines containing:

- `使用指挥官`
- `战术目标完成`

Render them as structured action summaries before falling back to raw logs.

- [ ] **Step 3: Smoke test viewer data loading**

Run:

```bash
cd prototypes/card-battle-sim
python3 export_match.py FRANCE RUSSIA 42
python3 -m http.server 8092 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8092/viewer.html
```

Manual checks:

- Commander names appear for both players.
- Objective names appear for both players.
- Used/completed states do not render as `undefined`.
- Existing controls still work.

Stop the server with `Ctrl-C`.

- [ ] **Step 4: Commit viewer update**

Run:

```bash
git add prototypes/card-battle-sim/viewer.html prototypes/card-battle-sim/match_data.json
git commit -m "feat: show command layer in replay viewer"
```

## Task 8: Objective Metrics And Balance Validation

**Files:**

- Modify: `prototypes/card-battle-sim/ecosystem_test.py`
- Modify: `prototypes/card-battle-sim/README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add objective completion metrics**

In `test_matchup`, after collecting `results`, count:

```python
    p1_objective_completed = sum(1 for r in results if getattr(r, "p1_objective_completed", False))
    p2_objective_completed = sum(1 for r in results if getattr(r, "p2_objective_completed", False))
```

Return:

```python
        "objective_completion_rate": (p1_objective_completed + p2_objective_completed) / (2 * n),
```

In `run_ecosystem_test`, print aggregate objective completion rate:

```python
    objective_completion_rate = statistics.mean(matrix[k]["objective_completion_rate"] for k in matrix)
    print(f"    目标完成率: {objective_completion_rate*100:.1f}%")
```

Add health warning:

```python
    if objective_completion_rate < 0.30 or objective_completion_rate > 0.75:
        issues.append(f"⚠️  目标完成率 {objective_completion_rate*100:.1f}% 不在 30%-75%")
```

- [ ] **Step 2: Run full verification**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py
python3 ecosystem_test.py 500 0
python3 ecosystem_test.py 500 500
```

Acceptance:

- Unit tests pass.
- Both ecosystem runs pass 45%-55% faction overall.
- Mirror first-player <=65%.
- France first-player vs Russia <=65%.
- PacingRisk <=0.30.
- No matchup average >21 turns.
- Objective completion rate 30%-75%.

- [ ] **Step 3: Apply bounded tuning if needed**

Use this order only:

1. If France exceeds 55% or France P1 vs Russia exceeds 65%, change Napoleon so the bonus cannot stack with Breakthrough Reward.
2. If Prussia exceeds 55%, change Blucher to buff at most 2 wounded units.
3. If Russia exceeds 55% or pacing worsens, remove Kutuzov's unit heal and keep only retreat + HQ +1.
4. If objective completion rate is above 75%, make the most common objective trigger stricter.
5. If objective completion rate is below 30%, make the least common objective reward trigger broader.

After each tuning change, run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py
python3 ecosystem_test.py 500 0
python3 ecosystem_test.py 500 500
```

Stop after these bounded tuning changes. If still failing, report exact metrics and do not add new systems.

- [ ] **Step 4: Update docs with final accepted metrics**

In `prototypes/card-battle-sim/README.md`, add v0.3A current baseline:

```markdown
**当前数据基线**（v0.3A: Command Layer + v0.2 作战压力/突破奖励，HQ 14）：
- HQ 起始血量：14
- 每阵营牌库：33 张
- 新机制：每阵营 1 名 Commander；每名玩家 1 个 Tactical Objective
- 主测试（`python3 ecosystem_test.py 500 0`）：使用最终输出中的三阵营胜率百分比
- 交叉验证（`python3 ecosystem_test.py 500 500`）：使用最终输出中的三阵营胜率百分比
- PacingRisk：使用最终两组输出中的 PacingRisk 数值
- 目标完成率：使用最终两组输出中的目标完成率
```

The committed README must contain exact numeric values from the final runs, not the instructional wording above.

In `AGENTS.md`, update Current State, balance baseline, unit test count, and known issues with final accepted values.

- [ ] **Step 5: Commit metrics/docs**

Run:

```bash
git add prototypes/card-battle-sim/ecosystem_test.py prototypes/card-battle-sim/README.md AGENTS.md
git commit -m "docs: record v0.3A command layer baseline"
```

## Task 9: Final Verification

**Files:**

- Read all modified files.

- [ ] **Step 1: Run unit tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py
```

Expected:

- All tests pass.

- [ ] **Step 2: Run ecosystem tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 ecosystem_test.py 500 0
python3 ecosystem_test.py 500 500
```

Expected:

- Both runs satisfy acceptance gates from this plan.

- [ ] **Step 3: Regenerate replay and PDF**

Run:

```bash
cd prototypes/card-battle-sim
python3 export_match.py FRANCE RUSSIA 42
python3 generate_pdf.py
```

Expected:

- `match_data.json` updated.
- `napoleon_cards.pdf` generated.

- [ ] **Step 4: Compile check**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m py_compile cards.py commanders.py objectives.py game.py ai.py combat.py game_state.py export_match.py ecosystem_test.py generate_pdf.py
```

Expected:

- Command exits 0 with no output.

- [ ] **Step 5: Final report**

Report these facts in plain text:

```text
Implemented v0.3A Command Layer: state whether commander, objective, export, and viewer work are all present.
Commanders: list active commanders and abilities.
Objectives: list active objectives and aggregate completion rate.
Unit tests: exact pass count.
Primary balance 500/0: overall rates, France P1 vs Russia, PacingRisk, objective completion, warnings.
Cross-check balance 500/500: overall rates, France P1 vs Russia, PacingRisk, objective completion, warnings.
Replay viewer: state whether commander/objective display was manually checked and list the local URL used.
Decision: PASS or NEEDS MORE TUNING.
Commits: list commit hashes.
```
