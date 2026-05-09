# Battlefield Situation Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a low-risk gameplay expansion pack (battlefield situations, commander reactions, unit synergies, shaken pressure) to the existing Napoleonic card battle simulator without changing deck sizes, HQ HP, or core victory settlement.

**Architecture:** Four feature-flagged layers built on existing seams: `game_state.py` for new state fields, `game.py` for situation cycling/reactions/pressure, `combat.py` for damage modifiers, `commanders.py` for reaction definitions, `export_match.py` for additive metadata. Each layer can be independently enabled/disabled.

**Tech Stack:** Python 3, unittest, existing simulator modules

**Spec:** `docs/superpowers/specs/2026-05-09-battlefield-situation-pack-design.md`

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `prototypes/card-battle-sim/game_state.py` | Modify | Add situation state, reaction state, pressure tracking |
| `prototypes/card-battle-sim/game.py` | Modify | Situation cycling, order bonus, advance surcharge, reactions, shaken pressure, feature flags |
| `prototypes/card-battle-sim/combat.py` | Modify | Dense fog modifier, synergy bonuses, cannon smoke |
| `prototypes/card-battle-sim/commanders.py` | Modify | Reaction definitions |
| `prototypes/card-battle-sim/export_match.py` | Modify | Additive metadata keys |
| `prototypes/card-battle-sim/test_rule_tuning.py` | Modify | New focused tests |
| `prototypes/card-battle-sim/test_viewer_export_contract.py` | Modify | Contract checks for new metadata |
| `prototypes/card-battle-sim/viewer.html` | Modify | Display new metadata in timeline/action panel |

---

## Task 1: Feature Flags And Situation State

**Files:**
- Modify: `prototypes/card-battle-sim/game_state.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Write failing tests for feature flags and situation state**

Add to `test_rule_tuning.py`:

```python
class BattlefieldSituationTests(unittest.TestCase):
    def test_feature_flags_exist_and_default_off(self):
        """Feature flags must exist and default to False."""
        import game
        self.assertFalse(getattr(game, 'ENABLE_BATTLEFIELD_SITUATIONS', True))
        self.assertFalse(getattr(game, 'ENABLE_COMMANDER_REACTIONS', True))
        self.assertFalse(getattr(game, 'ENABLE_UNIT_SYNERGIES', True))
        self.assertFalse(getattr(game, 'ENABLE_SHAKEN_PRESSURE', True))

    def test_battlefield_has_situation_state(self):
        """Battlefield must expose current_situation_id and situation_cycle."""
        bf = Battlefield()
        self.assertIsNone(bf.current_situation_id)
        self.assertIsInstance(bf.situation_cycle, list)
        self.assertEqual(len(bf.situation_cycle), 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_rule_tuning.py -k "BattlefieldSituationTests" -v`
Expected: FAIL (no such attributes)

- [ ] **Step 3: Add situation state to game_state.py**

Add to `Battlefield` class:

```python
# v0.5 Battlefield Situations
current_situation_id: Optional[str] = None
current_situation_started_turn: int = 0
situation_cycle: List[str] = field(default_factory=list)
```

- [ ] **Step 4: Add feature flags to game.py**

Add after `OPERATIONAL_PRESSURE_START_TURN`:

```python
# v0.5 feature flags
ENABLE_BATTLEFIELD_SITUATIONS = False
ENABLE_COMMANDER_REACTIONS = False
ENABLE_UNIT_SYNERGIES = False
ENABLE_SHAKEN_PRESSURE = False
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m unittest test_rule_tuning.py -k "BattlefieldSituationTests" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add prototypes/card-battle-sim/game_state.py prototypes/card-battle-sim/game.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat(situation-pack): add feature flags and battlefield situation state"
```

---

## Task 2: Situation Cycle Logic

**Files:**
- Modify: `prototypes/card-battle-sim/game.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Write failing tests for situation cycle**

Add to `BattlefieldSituationTests`:

```python
def test_situation_cycle_is_deterministic_by_seed(self):
    """Same seed produces same situation order."""
    from game import initialize_situation_cycle
    cycle_a = initialize_situation_cycle(42)
    cycle_b = initialize_situation_cycle(42)
    self.assertEqual(cycle_a, cycle_b)
    self.assertEqual(len(cycle_a), 4)
    self.assertEqual(set(cycle_a), {"dense_fog", "mud", "cannon_smoke", "stable_supply"})

def test_situation_cycle_different_seeds_differ(self):
    """Different seeds may produce different orders."""
    from game import initialize_situation_cycle
    cycle_a = initialize_situation_cycle(42)
    cycle_b = initialize_situation_cycle(7)
    # They may or may not differ, but both must be valid permutations
    self.assertEqual(set(cycle_a), set(cycle_b))

def test_advance_situation_starts_at_round_3(self):
    """First situation appears at round 3."""
    from game import get_situation_for_turn
    self.assertIsNone(get_situation_for_turn(0, ["dense_fog", "mud", "cannon_smoke", "stable_supply"]))
    self.assertIsNone(get_situation_for_turn(1, ["dense_fog", "mud", "cannon_smoke", "stable_supply"]))
    self.assertIsNone(get_situation_for_turn(2, ["dense_fog", "mud", "cannon_smoke", "stable_supply"]))
    self.assertEqual(get_situation_for_turn(3, ["dense_fog", "mud", "cannon_smoke", "stable_supply"]), "dense_fog")

def test_situation_advances_every_3_rounds(self):
    """Situations change every 3 full rounds: 3, 6, 9, 12."""
    cycle = ["dense_fog", "mud", "cannon_smoke", "stable_supply"]
    from game import get_situation_for_turn
    self.assertEqual(get_situation_for_turn(3, cycle), "dense_fog")
    self.assertEqual(get_situation_for_turn(4, cycle), "dense_fog")
    self.assertEqual(get_situation_for_turn(5, cycle), "dense_fog")
    self.assertEqual(get_situation_for_turn(6, cycle), "mud")
    self.assertEqual(get_situation_for_turn(9, cycle), "cannon_smoke")
    self.assertEqual(get_situation_for_turn(12, cycle), "stable_supply")
    # After all 4 shown, wraps around
    self.assertEqual(get_situation_for_turn(15, cycle), "dense_fog")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_rule_tuning.py -k "test_situation_cycle" -v`
Expected: FAIL

- [ ] **Step 3: Implement situation cycle functions in game.py**

Add after `OPERATIONAL_PRESSURE_START_TURN`:

```python
# v0.5 Battlefield Situations
SITUATION_IDS = ["dense_fog", "mud", "cannon_smoke", "stable_supply"]
SITUATION_START_ROUND = 3
SITUATION_DURATION_ROUNDS = 3


def initialize_situation_cycle(seed: int) -> list:
    """Return a deterministic permutation of SITUATION_IDS for this seed."""
    rng = random.Random(seed)
    cycle = list(SITUATION_IDS)
    rng.shuffle(cycle)
    return cycle


def get_situation_for_turn(turn_num: int, cycle: list) -> Optional[str]:
    """Return the situation ID active at this turn, or None if before start."""
    if not cycle or turn_num < SITUATION_START_ROUND:
        return None
    idx = ((turn_num - SITUATION_START_ROUND) // SITUATION_DURATION_ROUNDS) % len(cycle)
    return cycle[idx]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_rule_tuning.py -k "test_situation_cycle" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add prototypes/card-battle-sim/game.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat(situation-pack): add situation cycle logic"
```

---

## Task 3: Mud And Stable Supply Lines Effects

**Files:**
- Modify: `prototypes/card-battle-sim/game.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Write failing tests for Mud advance surcharge**

Add to `BattlefieldSituationTests`:

```python
def test_mud_costs_extra_order_for_cavalry_advance(self):
    """Cavalry advance costs +1 order during Mud."""
    bf = Battlefield()
    p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=STARTING_HQ_HP)
    p1.max_orders = 5
    p1.current_orders = 5
    cavalry = Card(name="测试骑兵", cost=2, attack=2, health=2,
                   unit_type=UnitType.CAVALRY, faction=Faction.FRANCE,
                   deploy_line=Line.REAR, keywords=[])
    unit = BattleUnit(card=cavalry, current_hp=2, current_line=Line.REAR, slot=1)
    bf.p1_rear.append(unit)
    bf.current_situation_id = "mud"
    # Cavalry advance should cost 2 (1 base + 1 mud)
    from game import get_advance_cost
    self.assertEqual(get_advance_cost(unit, bf), 2)

def test_mud_does_not_affect_infantry_advance(self):
    """Infantry advance costs normal 1 order during Mud."""
    bf = Battlefield()
    infantry = Card(name="测试步兵", cost=1, attack=1, health=1,
                    unit_type=UnitType.INFANTRY, faction=Faction.FRANCE,
                    deploy_line=Line.REAR, keywords=[])
    unit = BattleUnit(card=infantry, current_hp=1, current_line=Line.REAR, slot=1)
    bf.current_situation_id = "mud"
    from game import get_advance_cost
    self.assertEqual(get_advance_cost(unit, bf), 1)
```

- [ ] **Step 2: Write failing tests for Stable Supply Lines**

```python
def test_stable_supply_grants_extra_order(self):
    """Stable Supply Lines gives +1 current_orders, may exceed max_orders."""
    from game import apply_stable_supply_bonus
    p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=STARTING_HQ_HP)
    p1.max_orders = 5
    p1.current_orders = 5
    bf = Battlefield()
    bf.current_situation_id = "stable_supply"
    apply_stable_supply_bonus(p1, bf)
    self.assertEqual(p1.current_orders, 6)

def test_stable_supply_caps_at_max_orders(self):
    """Stable Supply Lines caps at MAX_ORDERS (16)."""
    from game import apply_stable_supply_bonus
    p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=STARTING_HQ_HP)
    p1.max_orders = MAX_ORDERS
    p1.current_orders = MAX_ORDERS
    bf = Battlefield()
    bf.current_situation_id = "stable_supply"
    apply_stable_supply_bonus(p1, bf)
    self.assertEqual(p1.current_orders, MAX_ORDERS)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m unittest test_rule_tuning.py -k "test_mud" -v`
Expected: FAIL

- [ ] **Step 4: Implement in game.py**

```python
def get_advance_cost(unit: BattleUnit, battlefield: Battlefield) -> int:
    """Return order cost to advance this unit. Mud adds +1 for cavalry."""
    cost = 1
    if battlefield.current_situation_id == "mud" and unit.card.unit_type == UnitType.CAVALRY:
        cost += 1
    return cost


def apply_stable_supply_bonus(player: Player, battlefield: Battlefield) -> None:
    """If Stable Supply Lines is active, grant +1 current_orders up to MAX_ORDERS."""
    if battlefield.current_situation_id != "stable_supply":
        return
    player.current_orders = min(player.current_orders + 1, MAX_ORDERS)
```

- [ ] **Step 5: Integrate situation cycle into play_turn**

In `play_turn()`, after `active.current_orders = active.max_orders` (line 394), add:

```python
    # v0.5: Update battlefield situation
    if ENABLE_BATTLEFIELD_SITUATIONS and battlefield.situation_cycle:
        old_situation = battlefield.current_situation_id
        battlefield.current_situation_id = get_situation_for_turn(turn_num, battlefield.situation_cycle)
        if battlefield.current_situation_id != old_situation:
            battlefield.current_situation_started_turn = turn_num
            if log is not None:
                SITUATION_NAMES = {"dense_fog": "浓雾", "mud": "泥泞", "cannon_smoke": "炮烟", "stable_supply": "补给线稳定"}
                log.append(f"  🌍 战场态势：{SITUATION_NAMES.get(battlefield.current_situation_id, battlefield.current_situation_id)}")
        # Apply Stable Supply Lines bonus
        apply_stable_supply_bonus(active, battlefield)
```

- [ ] **Step 6: Integrate Mud cost into advance phase**

In `play_turn()`, change the advance order checks from `if active.current_orders < 1:` to:

```python
        advance_cost = get_advance_cost(unit, battlefield) if ENABLE_BATTLEFIELD_SITUATIONS else 1
        if active.current_orders < advance_cost:
            continue
        ...
        active.current_orders -= advance_cost
```

Apply to both rear→main and main→skirmish advance loops.

- [ ] **Step 7: Initialize situation cycle in play_one_game**

In `play_one_game()`, after deck setup and before the turn loop, add:

```python
    if ENABLE_BATTLEFIELD_SITUATIONS:
        battlefield.situation_cycle = initialize_situation_cycle(seed)
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python3 -m unittest test_rule_tuning.py -k "test_mud or test_stable_supply" -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add prototypes/card-battle-sim/game.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat(situation-pack): add Mud cavalry surcharge and Stable Supply Lines order bonus"
```

---

## Task 4: Dense Fog And Cannon Smoke Effects

**Files:**
- Modify: `prototypes/card-battle-sim/combat.py`
- Modify: `prototypes/card-battle-sim/game.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Write failing tests for Dense Fog**

```python
def test_dense_fog_reduces_ranged_damage_by_1(self):
    """Ranged attackers deal -1 damage during Dense Fog."""
    bf = Battlefield()
    bf.current_situation_id = "dense_fog"
    artillery = Card(name="测试炮兵", cost=3, attack=3, health=3,
                     unit_type=UnitType.ARTILLERY, faction=Faction.FRANCE,
                     deploy_line=Line.REAR, keywords=["远程"])
    attacker = BattleUnit(card=artillery, current_hp=3, current_line=Line.REAR, slot=1)
    infantry = Card(name="测试步兵", cost=1, attack=1, health=3,
                    unit_type=UnitType.INFANTRY, faction=Faction.PRUSSIA,
                    deploy_line=Line.MAIN, keywords=[])
    defender = BattleUnit(card=infantry, current_hp=3, current_line=Line.MAIN, slot=1)
    from combat import calculate_damage_with_situation
    dmg_def, dmg_atk = calculate_damage_with_situation(attacker, defender, bf)
    # Base artillery attack 3, +1 vs infantry (not in formation), -1 fog = 3
    self.assertEqual(dmg_def, 3)

def test_dense_fog_does_not_reduce_non_ranged_damage(self):
    """Non-ranged attackers are unaffected by Dense Fog."""
    bf = Battlefield()
    bf.current_situation_id = "dense_fog"
    infantry_a = Card(name="攻击步兵", cost=1, attack=2, health=2,
                      unit_type=UnitType.INFANTRY, faction=Faction.FRANCE,
                      deploy_line=Line.MAIN, keywords=[])
    attacker = BattleUnit(card=infantry_a, current_hp=2, current_line=Line.MAIN, slot=1)
    infantry_d = Card(name="防御步兵", cost=1, attack=1, health=3,
                      unit_type=UnitType.INFANTRY, faction=Faction.PRUSSIA,
                      deploy_line=Line.MAIN, keywords=[])
    defender = BattleUnit(card=infantry_d, current_hp=3, current_line=Line.MAIN, slot=1)
    from combat import calculate_damage_with_situation
    dmg_def, _ = calculate_damage_with_situation(attacker, defender, bf)
    self.assertEqual(dmg_def, 2)  # No fog penalty
```

- [ ] **Step 2: Write failing tests for Cannon Smoke**

```python
def test_cannon_smoke_suppresses_first_qishe(self):
    """Cannon Smoke prevents 齐射 bonus on first attack this action."""
    bf = Battlefield()
    bf.current_situation_id = "cannon_smoke"
    # Player's first attack this action should not get 齐射
    # This test will be integrated with the attack count tracking
    from game import is_cannon_smoke_suppressed
    self.assertTrue(is_cannon_smoke_suppressed(bf, attacks_this_action=0))
    self.assertFalse(is_cannon_smoke_suppressed(bf, attacks_this_action=1))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m unittest test_rule_tuning.py -k "test_dense_fog or test_cannon_smoke" -v`
Expected: FAIL

- [ ] **Step 4: Implement damage modifier in combat.py**

Add after `effective_attack()`:

```python
def calculate_damage_with_situation(
    attacker: BattleUnit,
    defender: BattleUnit,
    battlefield: Battlefield,
    attacker_attack_override: Optional[int] = None,
    defender_attack_override: Optional[int] = None,
    cannon_smoke_suppresses_qishe: bool = False,
) -> Tuple[int, int]:
    """calculate_damage with battlefield situation modifiers applied.

    Modifier order: base → keyword → situation → synergy → evasion → final.
    """
    dmg_def, dmg_atk = calculate_damage(
        attacker, defender,
        attacker_attack_override=attacker_attack_override,
        defender_attack_override=defender_attack_override,
    )

    # Dense Fog: -1 ranged damage (minimum 1 if damage was positive)
    if battlefield.current_situation_id == "dense_fog":
        if "远程" in attacker.card.keywords and dmg_def > 0:
            dmg_def = max(1, dmg_def - 1)

    # Cannon Smoke: suppress 齐射 on first attack this action
    if cannon_smoke_suppresses_qishe and "齐射" in attacker.card.keywords:
        if not attacker.has_acted_this_turn:
            # The 齐射 bonus was +1 in calculate_damage; subtract it back
            dmg_def = max(0, dmg_def - 1)

    return (dmg_def, dmg_atk)
```

- [ ] **Step 5: Implement cannon smoke check in game.py**

```python
def is_cannon_smoke_suppressed(battlefield: Battlefield, attacks_this_action: int) -> bool:
    """Return True if Cannon Smoke should suppress 齐射 for this attack."""
    return battlefield.current_situation_id == "cannon_smoke" and attacks_this_action == 0
```

- [ ] **Step 6: Wire into execute_attack in combat.py**

In `execute_attack()`, when `ENABLE_BATTLEFIELD_SITUATIONS` is True, use `calculate_damage_with_situation` instead of `calculate_damage`. Pass `cannon_smoke_suppresses_qishe` from the caller.

Update `execute_attack` signature to accept `battlefield_situation_id: Optional[str] = None` and `cannon_smoke_suppresses_qishe: bool = False`.

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m unittest test_rule_tuning.py -k "test_dense_fog or test_cannon_smoke" -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add prototypes/card-battle-sim/combat.py prototypes/card-battle-sim/game.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat(situation-pack): add Dense Fog ranged penalty and Cannon Smoke 齐射 suppression"
```

---

## Task 5: Commander Reactions

**Files:**
- Modify: `prototypes/card-battle-sim/game_state.py`
- Modify: `prototypes/card-battle-sim/commanders.py`
- Modify: `prototypes/card-battle-sim/game.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Write failing tests for commander reactions**

```python
class CommanderReactionTests(unittest.TestCase):
    def test_commander_reaction_state_exists(self):
        """Player must have reaction_used and reaction_turn fields."""
        p = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        self.assertFalse(p.reaction_used)
        self.assertEqual(p.reaction_turn, 0)

    def test_napoleon_reaction_grants_order_on_hq_damage(self):
        """Napoleon reaction: +1 order when French unit first deals HQ damage."""
        bf = Battlefield()
        p1 = Player(name="P1-France", faction=Faction.FRANCE, hq_hp=14)
        p1.commander_id = "napoleon"
        p1.max_orders = 5
        p1.current_orders = 3
        p2 = Player(name="P2-Russia", faction=Faction.RUSSIA, hq_hp=14)
        from game import try_commander_reaction
        triggered = try_commander_reaction(p1, p2, bf, 0, "hq_damage", log=[])
        self.assertTrue(triggered)
        self.assertTrue(p1.reaction_used)
        self.assertEqual(p1.current_orders, 4)  # +1 order

    def test_commander_reaction_fires_only_once(self):
        """Each commander reaction can only fire once per match."""
        bf = Battlefield()
        p1 = Player(name="P1-France", faction=Faction.FRANCE, hq_hp=14)
        p1.commander_id = "napoleon"
        p1.max_orders = 5
        p1.current_orders = 3
        p2 = Player(name="P2-Russia", faction=Faction.RUSSIA, hq_hp=14)
        from game import try_commander_reaction
        try_commander_reaction(p1, p2, bf, 0, "hq_damage", log=[])
        # Second trigger should not fire
        p1.current_orders = 3
        triggered = try_commander_reaction(p1, p2, bf, 0, "hq_damage", log=[])
        self.assertFalse(triggered)
        self.assertEqual(p1.current_orders, 3)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_rule_tuning.py -k "CommanderReactionTests" -v`
Expected: FAIL

- [ ] **Step 3: Add reaction state to Player in game_state.py**

Add to `Player` class after `play_log`:

```python
    # v0.5 Commander Reactions
    reaction_used: bool = False
    reaction_turn: int = 0
```

- [ ] **Step 4: Add reaction definitions to commanders.py**

```python
@dataclass(frozen=True)
class CommanderReaction:
    id: str
    trigger: str  # "hq_damage", "main_line_empty", "hq_damaged"
    description: str


COMMANDER_REACTIONS = {
    CommanderId.NAPOLEON: CommanderReaction(
        id="opportunity_seized",
        trigger="hq_damage",
        description="首次造成 HQ 伤害时，+1 军令",
    ),
    CommanderId.BLUCHER: CommanderReaction(
        id="rally_militia",
        trigger="main_line_empty",
        description="首次主力线被清空时，后方生成 1/2 后备国民军",
    ),
    CommanderId.KUTUZOV: CommanderReaction(
        id="strategic_retreat",
        trigger="hq_damaged",
        description="首次 HQ 受伤时，治疗最受伤友军 1 HP",
    ),
}
```

- [ ] **Step 5: Implement try_commander_reaction in game.py**

```python
def try_commander_reaction(
    player: Player, opponent: Player, battlefield: Battlefield,
    player_idx: int, trigger: str, log: list = None,
) -> bool:
    """Attempt to fire a commander reaction. Returns True if triggered."""
    if not ENABLE_COMMANDER_REACTIONS:
        return False
    if player.reaction_used:
        return False
    from commanders import COMMANDER_REACTIONS, CommanderId
    try:
        cmd_id = CommanderId(player.commander_id)
    except (ValueError, KeyError):
        return False
    reaction = COMMANDER_REACTIONS.get(cmd_id)
    if not reaction or reaction.trigger != trigger:
        return False

    player.reaction_used = True
    player.reaction_turn = 0  # Will be set by caller

    if cmd_id == CommanderId.NAPOLEON:
        player.current_orders = min(player.current_orders + 1, MAX_ORDERS)
        if log:
            log.append(f"  ⚜ 拿破仑反应「战机捕捉」：+1 军令（现{player.current_orders}）")

    elif cmd_id == CommanderId.BLUCHER:
        bf_line = battlefield.get_line(player_idx, Line.REAR)
        if len(bf_line) < battlefield.LINE_CAPACITY:
            from cards import Card, UnitType
            token_card = Card(
                name="后备国民军", cost=0, attack=1, health=2,
                unit_type=UnitType.INFANTRY, faction=player.faction,
                deploy_line=Line.REAR, keywords=[],
            )
            slot = battlefield.choose_deploy_slot(player_idx, Line.REAR)
            if slot is not None:
                token_unit = BattleUnit(card=token_card, current_hp=2, current_line=Line.REAR, slot=slot)
                bf_line.append(token_unit)
                battlefield.sort_line(player_idx, Line.REAR)
                if log:
                    log.append(f"  ⚜ 布吕歇尔反应「顽强集结」：后方生成后备国民军 槽位{slot+1}")
        else:
            player.current_orders = min(player.current_orders + 1, MAX_ORDERS)
            if log:
                log.append(f"  ⚜ 布吕歇尔反应「顽强集结」：后方已满，+1 军令")

    elif cmd_id == CommanderId.KUTUZOV:
        units = battlefield.all_units(player_idx)
        damaged = [u for u in units if u.current_hp < u.base_max_hp and not u.is_dead]
        if damaged:
            target = min(damaged, key=lambda u: u.current_hp)
            target.current_hp = min(target.current_hp + 1, target.base_max_hp)
            if log:
                log.append(f"  ⚜ 库图佐夫反应「深纵回撤」：{target.card.name} 恢复 1 HP（现{target.current_hp}）")
        else:
            player.hq_hp = min(player.hq_hp + 1, STARTING_HQ_HP)
            if log:
                log.append(f"  ⚜ 库图佐夫反应「深纵回撤」：无受伤友军，HQ 恢复 1（现{player.hq_hp}）")

    return True
```

- [ ] **Step 6: Wire reactions into play_turn**

- After `hq_damage_dealt > 0` in attack phase: call `try_commander_reaction(active, opponent, battlefield, active_idx, "hq_damage", log)`
- After main line is cleared: call with trigger `"main_line_empty"`
- When HQ takes damage: call with trigger `"hq_damaged"` for the defender

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m unittest test_rule_tuning.py -k "CommanderReactionTests" -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add prototypes/card-battle-sim/game_state.py prototypes/card-battle-sim/commanders.py prototypes/card-battle-sim/game.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat(situation-pack): add commander reactions (Napoleon/Blücher/Kutuzov)"
```

---

## Task 6: Unit Synergies

**Files:**
- Modify: `prototypes/card-battle-sim/combat.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Write failing tests for synergies**

```python
class UnitSynergyTests(unittest.TestCase):
    def test_infantry_artillery_synergy_bonus(self):
        """Artillery with infantry in same slot in main/rear gets +1 unit damage."""
        bf = Battlefield()
        artillery = Card(name="炮兵", cost=3, attack=3, health=3,
                         unit_type=UnitType.ARTILLERY, faction=Faction.FRANCE,
                         deploy_line=Line.REAR, keywords=["远程"])
        arty_unit = BattleUnit(card=artillery, current_hp=3, current_line=Line.REAR, slot=1)
        infantry = Card(name="步兵", cost=1, attack=2, health=3,
                        unit_type=UnitType.INFANTRY, faction=Faction.FRANCE,
                        deploy_line=Line.MAIN, keywords=[])
        inf_unit = BattleUnit(card=infantry, current_hp=3, current_line=Line.MAIN, slot=1)
        bf.p1_rear = [arty_unit]
        bf.p1_main = [inf_unit]
        target = Card(name="敌步兵", cost=1, attack=1, health=3,
                      unit_type=UnitType.INFANTRY, faction=Faction.PRUSSIA,
                      deploy_line=Line.MAIN, keywords=[])
        defender = BattleUnit(card=target, current_hp=3, current_line=Line.MAIN, slot=1)
        bf.p2_main = [defender]
        from combat import apply_synergy_bonus
        bonus = apply_synergy_bonus(arty_unit, defender, bf, 0)
        self.assertEqual(bonus, 1)

    def test_cavalry_vs_shaken_synergy(self):
        """Cavalry attacking Shaken unit gets +1 damage."""
        bf = Battlefield()
        cavalry = Card(name="骑兵", cost=2, attack=2, health=2,
                       unit_type=UnitType.CAVALRY, faction=Faction.FRANCE,
                       deploy_line=Line.REAR, keywords=[])
        cav_unit = BattleUnit(card=cavalry, current_hp=2, current_line=Line.MAIN, slot=1)
        target = Card(name="敌步兵", cost=1, attack=1, health=3,
                      unit_type=UnitType.INFANTRY, faction=Faction.PRUSSIA,
                      deploy_line=Line.MAIN, keywords=[])
        defender = BattleUnit(card=target, current_hp=1, current_line=Line.MAIN, slot=1)
        defender.is_shaken = True
        from combat import apply_synergy_bonus
        bonus = apply_synergy_bonus(cav_unit, defender, bf, 0)
        self.assertEqual(bonus, 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_rule_tuning.py -k "UnitSynergyTests" -v`
Expected: FAIL

- [ ] **Step 3: Implement apply_synergy_bonus in combat.py**

```python
def apply_synergy_bonus(
    attacker: BattleUnit, defender: BattleUnit,
    battlefield: Battlefield, attacker_player_idx: int,
) -> int:
    """Return total synergy damage bonus for this attack. Max 1 synergy bonus per attack."""
    if not battlefield.current_situation_id:  # Only active when situations enabled
        return 0

    # Infantry + Artillery: artillery gets +1 vs units if infantry in same slot
    if attacker.card.unit_type == UnitType.ARTILLERY:
        for line in (Line.REAR, Line.MAIN):
            for friendly in battlefield.get_line(attacker_player_idx, line):
                if (friendly.slot == attacker.slot
                        and friendly.card.unit_type == UnitType.INFANTRY):
                    return 1

    # Cavalry vs Shaken: +1 damage
    if attacker.card.unit_type == UnitType.CAVALRY and defender.is_shaken:
        return 1

    return 0
```

- [ ] **Step 4: Wire into execute_attack**

When `ENABLE_UNIT_SYNERGIES` is True, add synergy bonus to damage calculation.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m unittest test_rule_tuning.py -k "UnitSynergyTests" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add prototypes/card-battle-sim/combat.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat(situation-pack): add Infantry+Artillery and Cavalry vs Shaken synergies"
```

---

## Task 7: Shaken Pressure

**Files:**
- Modify: `prototypes/card-battle-sim/combat.py`
- Modify: `prototypes/card-battle-sim/game_state.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Write failing tests for shaken pressure**

```python
class ShakenPressureTests(unittest.TestCase):
    def test_pressure_active_when_hq_low(self):
        """Player is under pressure when HQ <= 7."""
        from combat import is_under_morale_pressure
        p = Player(name="P1", faction=Faction.FRANCE, hq_hp=7)
        bf = Battlefield()
        self.assertTrue(is_under_morale_pressure(p, bf, 0))

    def test_pressure_active_when_lost_2_units_this_round(self):
        """Player is under pressure when 2+ units lost this full round."""
        from combat import is_under_morale_pressure
        p = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        bf = Battlefield()
        bf.p1_units_lost_this_round = 2
        self.assertTrue(is_under_morale_pressure(p, bf, 0))

    def test_pressure_lower_damage_threshold(self):
        """Under pressure, 1+ damage at half HP triggers Shaken (vs normal 2+)."""
        from combat import maybe_mark_shaken_with_pressure
        unit = BattleUnit(card=Card(name="测试", cost=1, attack=1, health=4,
                                     unit_type=UnitType.INFANTRY, faction=Faction.FRANCE,
                                     deploy_line=Line.MAIN, keywords=[]),
                          current_hp=2, current_line=Line.MAIN, slot=1)
        result = maybe_mark_shaken_with_pressure(unit, damage_taken=1, under_pressure=True, log=[])
        self.assertTrue(result)
        self.assertTrue(unit.is_shaken)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_rule_tuning.py -k "ShakenPressureTests" -v`
Expected: FAIL

- [ ] **Step 3: Add tracking to Battlefield**

```python
# v0.5 Shaken Pressure tracking
p1_units_lost_this_round: int = 0
p2_units_lost_this_round: int = 0
```

- [ ] **Step 4: Implement in combat.py**

```python
def is_under_morale_pressure(player: Player, battlefield: Battlefield, player_idx: int) -> bool:
    """Return True if player meets Shaken Pressure conditions."""
    if player.hq_hp <= 7:
        return True
    lost = battlefield.p1_units_lost_this_round if player_idx == 0 else battlefield.p2_units_lost_this_round
    return lost >= 2


def maybe_mark_shaken_with_pressure(unit: BattleUnit, damage_taken: int,
                                     under_pressure: bool, log: list = None) -> bool:
    """Apply Shaken with reduced threshold when under pressure."""
    if unit.is_dead:
        return False
    threshold = 1 if under_pressure else 2
    if damage_taken < threshold:
        return False
    if unit.current_hp * 2 > unit.base_max_hp:
        return False
    if not unit.mark_shaken():
        return False
    if log is not None:
        log.append(f"  ⚑ {unit.card.name} 动摇")
    return True
```

- [ ] **Step 5: Wire into execute_attack and round tracking**

In `execute_attack()`, when `ENABLE_SHAKEN_PRESSURE` is True, use `maybe_mark_shaken_with_pressure` instead of `maybe_mark_shaken`.

In `play_one_game()`, reset `battlefield.p1_units_lost_this_round = 0` and `p2_units_lost_this_round = 0` at the start of each full round. Increment when units die.

- [ ] **Step 6: Run tests to verify they pass**

Run: `python3 -m unittest test_rule_tuning.py -k "ShakenPressureTests" -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add prototypes/card-battle-sim/combat.py prototypes/card-battle-sim/game_state.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "feat(situation-pack): add Shaken Pressure with reduced damage threshold"
```

---

## Task 8: Export Metadata And Viewer Contract

**Files:**
- Modify: `prototypes/card-battle-sim/export_match.py`
- Modify: `prototypes/card-battle-sim/test_viewer_export_contract.py`

- [ ] **Step 1: Write failing contract tests**

Add to `test_viewer_export_contract.py`:

```python
def test_export_includes_battlefield_situation_when_enabled(self):
    """Export must include battlefield_situation key when situations are enabled."""
    # This test runs with feature flags enabled via patching
    import game
    with patch.object(game, 'ENABLE_BATTLEFIELD_SITUATIONS', True):
        data = play_and_export(Faction.FRANCE, Faction.RUSSIA, 42)
        # Check that at least one timeline step has battlefield_situation
        has_situation = any(
            step.get("battlefield_situation") is not None
            for step in data["timeline"]
        )
        self.assertTrue(has_situation)

def test_export_includes_commander_reaction_when_enabled(self):
    """Export must include commander_reaction key when reactions fire."""
    # Check structure exists in export code
    import export_match
    source = open(export_match.__file__).read()
    self.assertIn("commander_reaction", source)

def test_export_includes_damage_modifiers(self):
    """Export must include damage_modifiers array for situation/synergy modifiers."""
    import export_match
    source = open(export_match.__file__).read()
    self.assertIn("damage_modifiers", source)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_viewer_export_contract.py -k "battlefield_situation" -v`
Expected: FAIL

- [ ] **Step 3: Add metadata to export_match.py**

In `snapshot_battlefield()`, add after `ui_summary`:

```python
    # v0.5 Battlefield Situation metadata
    if bf.current_situation_id:
        SITUATION_NAMES = {"dense_fog": "浓雾", "mud": "泥泞", "cannon_smoke": "炮烟", "stable_supply": "补给线稳定"}
        result["battlefield_situation"] = {
            "id": bf.current_situation_id,
            "name": SITUATION_NAMES.get(bf.current_situation_id, bf.current_situation_id),
            "started_turn": bf.current_situation_started_turn,
        }
    else:
        result["battlefield_situation"] = None
```

Add `commander_reaction` and `damage_modifiers` as optional keys in the timeline step builder.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_viewer_export_contract.py -v`
Expected: PASS (all existing + new)

- [ ] **Step 5: Commit**

```bash
git add prototypes/card-battle-sim/export_match.py prototypes/card-battle-sim/test_viewer_export_contract.py
git commit -m "feat(situation-pack): add export metadata for situations, reactions, and damage modifiers"
```

---

## Task 9: Viewer Display

**Files:**
- Modify: `prototypes/card-battle-sim/viewer.html`

- [ ] **Step 1: Add situation display to action panel**

In the `renderActionSummary()` function, add a situation badge when `battlefield_situation` is present in the timeline step.

- [ ] **Step 2: Add situation change events to timeline**

In `buildTimeline()`, detect situation changes and render them as event cards with type `"situation"`.

- [ ] **Step 3: Add commander reaction event cards**

Detect `commander_reaction` in timeline steps and render as event cards.

- [ ] **Step 4: Add damage modifier annotations**

When `damage_modifiers` is present in an attack step, show modifier breakdown in the action summary.

- [ ] **Step 5: Run viewer/export contract tests**

Run: `python3 -m unittest test_viewer_export_contract.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add prototypes/card-battle-sim/viewer.html
git commit -m "feat(situation-pack): display battlefield situations and reactions in viewer"
```

---

## Task 10: Enable Feature Flags And Balance Check

**Files:**
- Modify: `prototypes/card-battle-sim/game.py`

- [ ] **Step 1: Enable all feature flags**

```python
ENABLE_BATTLEFIELD_SITUATIONS = True
ENABLE_COMMANDER_REACTIONS = True
ENABLE_UNIT_SYNERGIES = True
ENABLE_SHAKEN_PRESSURE = True
```

- [ ] **Step 2: Run full test suite**

Run: `python3 -m unittest test_rule_tuning.py test_viewer_export_contract.py -v`
Expected: ALL PASS

- [ ] **Step 3: Run ecosystem balance check**

Run: `python3 ecosystem_test.py 500 0`
Expected: PacingRisk <= 0.30, faction win rates 45%-55%, mirror first-player <= 65%

- [ ] **Step 4: Run 500/500 cross-seed check**

Run: `python3 ecosystem_test.py 500 500`
Expected: Same acceptance bands

- [ ] **Step 5: Export sample matches for viewer verification**

Run:
```bash
python3 export_match.py FRANCE RUSSIA 42
python3 export_match.py PRUSSIA RUSSIA 7
python3 export_match.py FRANCE PRUSSIA 10
```

Verify viewer at `http://localhost:8000/viewer.html` shows situation changes and reactions.

- [ ] **Step 6: Tune if needed**

If balance is outside bands:
- Adjust situation start round (3 → 4 or 5)
- Adjust Dense Fog penalty (-1 → no change)
- Adjust Stable Supply bonus (+1 → 0, i.e., disable)
- Adjust Shaken Pressure threshold (7 → 5 HP)
- Disable `ENABLE_SHAKEN_PRESSURE` first if needed

- [ ] **Step 7: Final commit**

```bash
git add prototypes/card-battle-sim/game.py
git commit -m "feat(situation-pack): enable all feature flags after balance verification"
```
