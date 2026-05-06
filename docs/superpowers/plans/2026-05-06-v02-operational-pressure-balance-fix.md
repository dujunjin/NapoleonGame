# v0.2 Operational Pressure And Balance Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the v0.2 acceptance blockers: Operational Pressure damages the wrong HQ, ecosystem health uses the wrong balance thresholds, and the final v0.2 balance must satisfy the product spec.

**Architecture:** Keep v0.2 scoped to pacing and balance. Extract Operational Pressure into a small helper in `game.py` so it can be unit-tested directly, keep the current `turn 18+` implementation if balance testing supports it, and document that explicit deviation from the product design's original turn 15 recommendation. Do not add v0.3 systems, commanders, campaign, deckbuilding, or fourth faction work.

**Tech Stack:** Python `unittest`, deterministic simulator in `prototypes/card-battle-sim`, balance verification through `ecosystem_test.py`, documentation in Markdown.

---

## Current Failure Summary

The previous v0.2 implementation is not accepted.

Verified failures:

- `game.py` Operational Pressure damages the player who did deal HQ damage instead of the player who failed to deal HQ damage.
- `ecosystem_test.py` prints a green health verdict using 40%-60% faction thresholds, while the v0.2 product spec requires 45%-55%.
- `ecosystem_test.py` computes pacing metric denominators as `n * 6`, but the matrix runs 3x3 = 9 matchup groups. Use `n * len(factions) * len(factions)` for total games.
- Fresh ecosystem tests failed v0.2 balance:
  - `python3 ecosystem_test.py 500 0`: France 45.1%, Prussia 58.1%, Russia 46.8%.
  - `python3 ecosystem_test.py 500 500`: France 44.0%, Prussia 58.7%, Russia 47.2%.
- Current implementation uses Operational Pressure from turn 18, while `docs/superpowers/specs/2026-05-06-napoleon-v02-v04-product-design.md` says turn 15.

Final acceptance requires:

- `python3 -m unittest test_rule_tuning.py` passes.
- `python3 ecosystem_test.py 500 0` has all faction overall rates in 45%-55%.
- `python3 ecosystem_test.py 500 500` has all faction overall rates in 45%-55%.
- All mirror first-player rates are <=65%.
- France first-player vs Russia is <=65%.
- No matchup average exceeds 21 turns.
- PacingRisk is <=0.30 in both ecosystem runs.
- If Operational Pressure remains turn 18, the product design and README/AGENTS docs must say turn 18 and explain that it is the implemented tuning value.

## File Structure

Modify:

- `prototypes/card-battle-sim/game.py`
  - Add `OPERATIONAL_PRESSURE_START_TURN = 18`.
  - Add `apply_operational_pressure(...)`.
  - Replace inline pressure logic with helper call.

- `prototypes/card-battle-sim/test_rule_tuning.py`
  - Add direct unit tests for Operational Pressure:
    - before pressure turn.
    - only P1 dealt HQ damage.
    - only P2 dealt HQ damage.
    - both dealt HQ damage.
    - neither dealt HQ damage.

- `prototypes/card-battle-sim/ecosystem_test.py`
  - Change faction health thresholds from 40%-60% to 45%-55%.
  - Add health checks for mirror first-player >65%.
  - Add health check for France first-player vs Russia >65%.
  - Fix pacing metric denominator from 6 matchup groups to 9 matchup groups.

- `prototypes/card-battle-sim/cards.py`
  - Modify only if balance still fails after the pressure bug and ecosystem thresholds are fixed.
  - Preferred tuning: weaken Prussia's draw/buff event before buffing other factions.

- `prototypes/card-battle-sim/README.md`
  - Update v0.2 result block after final balance pass.

- `AGENTS.md`
  - Update current state and known issues after final balance pass.

- `docs/superpowers/specs/2026-05-06-napoleon-v02-v04-product-design.md`
  - If keeping turn 18, update the Operational Pressure section from turn 15 to turn 18 and add the reason.

Do not modify:

- v0.3 commander, campaign, event-category, or deckbuilding systems.
- v0.4 fourth faction design.
- HQ HP.
- Deck size.
- Viewer visual redesign beyond required labels for existing v0.2 data.

## Task 1: Add Failing Operational Pressure Unit Tests

**Files:**

- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

- [ ] **Step 1: Update the game import**

Change the import near the top from:

```python
from game import deploy_card, play_turn, play_one_game, advance_max_orders, MAX_ORDERS, STARTING_HQ_HP, MAX_TURNS
```

to:

```python
from game import (
    deploy_card, play_turn, play_one_game, advance_max_orders,
    apply_operational_pressure,
    MAX_ORDERS, STARTING_HQ_HP, MAX_TURNS, OPERATIONAL_PRESSURE_START_TURN,
)
```

- [ ] **Step 2: Add tests after `test_global_constants_pinned`**

Add this complete test block:

```python
    def test_operational_pressure_does_not_apply_before_start_turn(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []

        apply_operational_pressure(
            p1, p2,
            p1_dealt_hq_damage=False,
            p2_dealt_hq_damage=False,
            turn=OPERATIONAL_PRESSURE_START_TURN - 1,
            log=log,
        )

        self.assertEqual((p1.hq_hp, p2.hq_hp), (14, 14))
        self.assertEqual(log, [])

    def test_operational_pressure_penalizes_p2_when_only_p1_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []

        apply_operational_pressure(
            p1, p2,
            p1_dealt_hq_damage=True,
            p2_dealt_hq_damage=False,
            turn=OPERATIONAL_PRESSURE_START_TURN,
            log=log,
        )

        self.assertEqual((p1.hq_hp, p2.hq_hp), (14, 13))
        self.assertIn("P2 未造成 HQ 伤害，HQ -1", log[-1])

    def test_operational_pressure_penalizes_p1_when_only_p2_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []

        apply_operational_pressure(
            p1, p2,
            p1_dealt_hq_damage=False,
            p2_dealt_hq_damage=True,
            turn=OPERATIONAL_PRESSURE_START_TURN,
            log=log,
        )

        self.assertEqual((p1.hq_hp, p2.hq_hp), (13, 14))
        self.assertIn("P1 未造成 HQ 伤害，HQ -1", log[-1])

    def test_operational_pressure_does_not_apply_when_both_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []

        apply_operational_pressure(
            p1, p2,
            p1_dealt_hq_damage=True,
            p2_dealt_hq_damage=True,
            turn=OPERATIONAL_PRESSURE_START_TURN,
            log=log,
        )

        self.assertEqual((p1.hq_hp, p2.hq_hp), (14, 14))
        self.assertEqual(log, [])

    def test_operational_pressure_penalizes_both_when_neither_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []

        apply_operational_pressure(
            p1, p2,
            p1_dealt_hq_damage=False,
            p2_dealt_hq_damage=False,
            turn=OPERATIONAL_PRESSURE_START_TURN,
            log=log,
        )

        self.assertEqual((p1.hq_hp, p2.hq_hp), (13, 13))
        self.assertIn("双方均未造成 HQ 伤害，各 HQ -1", log[-1])
```

- [ ] **Step 3: Run the new tests and confirm they fail**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_does_not_apply_before_start_turn \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_penalizes_p2_when_only_p1_dealt_hq_damage \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_penalizes_p1_when_only_p2_dealt_hq_damage \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_does_not_apply_when_both_dealt_hq_damage \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_penalizes_both_when_neither_dealt_hq_damage
```

Expected before implementation:

- Import fails because `apply_operational_pressure` and `OPERATIONAL_PRESSURE_START_TURN` do not exist.

## Task 2: Fix Operational Pressure Direction

**Files:**

- Modify: `prototypes/card-battle-sim/game.py`

- [ ] **Step 1: Add pressure constant near global constants**

Find the constants near the top of `game.py`. Add:

```python
OPERATIONAL_PRESSURE_START_TURN = 18
```

Keep `MAX_TURNS`, `STARTING_HQ_HP`, and deck constants unchanged.

- [ ] **Step 2: Add helper before `play_one_game`**

Add this function above `play_one_game`:

```python
def apply_operational_pressure(p1: Player, p2: Player,
                               p1_dealt_hq_damage: bool,
                               p2_dealt_hq_damage: bool,
                               turn: int,
                               log: Optional[List[str]] = None) -> None:
    """Apply round-end pressure to players who failed to damage enemy HQ."""
    if turn < OPERATIONAL_PRESSURE_START_TURN:
        return

    if p1_dealt_hq_damage and not p2_dealt_hq_damage:
        p2.hq_hp -= 1
        if log is not None:
            log.append(f"  ⚡ 作战压力：{p2.name} 未造成 HQ 伤害，HQ -1")
    elif p2_dealt_hq_damage and not p1_dealt_hq_damage:
        p1.hq_hp -= 1
        if log is not None:
            log.append(f"  ⚡ 作战压力：{p1.name} 未造成 HQ 伤害，HQ -1")
    elif not p1_dealt_hq_damage and not p2_dealt_hq_damage:
        p1.hq_hp -= 1
        p2.hq_hp -= 1
        if log is not None:
            log.append("  ⚡ 作战压力：双方均未造成 HQ 伤害，各 HQ -1")
```

- [ ] **Step 3: Replace inline pressure logic in `play_one_game`**

Replace the current block:

```python
        # 作战压力（Operational Pressure）：turn 18+ 时，未对敌方 HQ 造成伤害的一方受到 1 点压力伤害
        if turn >= 18:
            if p1_dealt_hq_damage and not p2_dealt_hq_damage:
                p1.hq_hp -= 1
                if log is not None:
                    log.append(f"  ⚡ 作战压力：{p2.name} 未造成 HQ 伤害，HQ -1")
            elif p2_dealt_hq_damage and not p1_dealt_hq_damage:
                p2.hq_hp -= 1
                if log is not None:
                    log.append(f"  ⚡ 作战压力：{p1.name} 未造成 HQ 伤害，HQ -1")
            elif not p1_dealt_hq_damage and not p2_dealt_hq_damage:
                p1.hq_hp -= 1
                p2.hq_hp -= 1
                if log is not None:
                    log.append(f"  ⚡ 作战压力：双方均未造成 HQ 伤害，各 HQ -1")
```

with:

```python
        # 作战压力（Operational Pressure）：未对敌方 HQ 造成伤害的一方受到 1 点压力伤害
        apply_operational_pressure(
            p1, p2,
            p1_dealt_hq_damage=p1_dealt_hq_damage,
            p2_dealt_hq_damage=p2_dealt_hq_damage,
            turn=turn,
            log=log,
        )
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_does_not_apply_before_start_turn \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_penalizes_p2_when_only_p1_dealt_hq_damage \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_penalizes_p1_when_only_p2_dealt_hq_damage \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_does_not_apply_when_both_dealt_hq_damage \
  test_rule_tuning.RuleTuningTests.test_operational_pressure_penalizes_both_when_neither_dealt_hq_damage
```

Expected:

- 5 tests pass.

- [ ] **Step 5: Run full unit tests**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py
```

Expected:

- All tests pass.

## Task 3: Fix Ecosystem Health Thresholds

**Files:**

- Modify: `prototypes/card-battle-sim/ecosystem_test.py`

- [ ] **Step 1: Add explicit health constants near imports**

After imports, add:

```python
MIN_HEALTHY_OVERALL = 0.45
MAX_HEALTHY_OVERALL = 0.55
MAX_MIRROR_FIRST_PLAYER = 0.65
MAX_FRANCE_P1_VS_RUSSIA = 0.65
MAX_PACING_RISK = 0.30
MAX_TIMEOUT_RATE = 0.03
MAX_MATCHUP_AVG_TURNS = 21.0
```

- [ ] **Step 2: Change faction overall threshold checks**

Replace:

```python
        if overall < 0.40:
            issues.append(f"⚠️  {f.value} 综合胜率 {overall*100:.1f}% 偏低")
        if overall > 0.60:
            issues.append(f"⚠️  {f.value} 综合胜率 {overall*100:.1f}% 偏高")
```

with:

```python
        if overall < MIN_HEALTHY_OVERALL:
            issues.append(f"⚠️  {f.value} 综合胜率 {overall*100:.1f}% < 45%")
        if overall > MAX_HEALTHY_OVERALL:
            issues.append(f"⚠️  {f.value} 综合胜率 {overall*100:.1f}% > 55%")
```

- [ ] **Step 3: Change timeout, average-turns, and pacing thresholds to constants**

Replace:

```python
    total_games = n * 6
```

with:

```python
    total_games = n * len(factions) * len(factions)
```

Keep `total_timeouts`, `total_long`, `overall_avg_turns`, `timeout_rate`, `long_game_rate`, and `pacing_risk` derived from this corrected `total_games`.

Replace:

```python
    if timeout_rate > 0.03:
        issues.append(f"⚠️  超时率 {timeout_rate*100:.1f}% > 3%")
```

with:

```python
    if timeout_rate > MAX_TIMEOUT_RATE:
        issues.append(f"⚠️  超时率 {timeout_rate*100:.1f}% > 3%")
```

Replace:

```python
        if stats["avg_turns"] > 21:
            issues.append(f"⚠️  {k[0].value} vs {k[1].value} 平均 {stats['avg_turns']:.1f} 回合，过长")
```

with:

```python
        if stats["avg_turns"] > MAX_MATCHUP_AVG_TURNS:
            issues.append(f"⚠️  {k[0].value} vs {k[1].value} 平均 {stats['avg_turns']:.1f} 回合，过长")
```

Replace:

```python
    if pacing_risk > 0.30:
        issues.append(f"⚠️  PacingRisk {pacing_risk:.3f} > 0.30")
```

with:

```python
    if pacing_risk > MAX_PACING_RISK:
        issues.append(f"⚠️  PacingRisk {pacing_risk:.3f} > 0.30")
```

- [ ] **Step 4: Add mirror and France-vs-Russia health checks**

After the average-turns loop, add:

```python
    for faction in factions:
        mirror_wr = matrix[(faction, faction)]["p1_winrate"]
        if mirror_wr > MAX_MIRROR_FIRST_PLAYER:
            issues.append(f"⚠️  {faction.value} mirror first-player {mirror_wr*100:.1f}% > 65%")

    france_vs_russia = matrix[(Faction.FRANCE, Faction.RUSSIA)]["p1_winrate"]
    if france_vs_russia > MAX_FRANCE_P1_VS_RUSSIA:
        issues.append(f"⚠️  法兰西先手 vs 俄罗斯 {france_vs_russia*100:.1f}% > 65%")
```

- [ ] **Step 5: Run ecosystem smoke test**

Run:

```bash
cd prototypes/card-battle-sim
python3 ecosystem_test.py 50 0
```

Expected:

- Command exits 0.
- Output still prints matrix, overall rates, pacing metrics, and health assessment.
- If a faction falls outside 45%-55%, output must show a warning instead of printing only `✅ 三阵营生态健康`.

- [ ] **Step 6: Commit test and threshold fixes**

Run:

```bash
git add prototypes/card-battle-sim/game.py prototypes/card-battle-sim/test_rule_tuning.py prototypes/card-battle-sim/ecosystem_test.py
git commit -m "fix: correct operational pressure validation"
```

## Task 4: Re-run Balance After Correct Pressure Direction

**Files:**

- Read: `prototypes/card-battle-sim/ecosystem_test.py`
- Modify: no files unless thresholds fail.

- [ ] **Step 1: Run primary ecosystem test**

Run:

```bash
cd prototypes/card-battle-sim
python3 ecosystem_test.py 500 0
```

Record:

- 3x3 matchup matrix.
- Overall faction rates.
- Mirror first-player rates.
- France first-player vs Russia.
- Timeout rate.
- Long-game rate.
- Average turns.
- PacingRisk.
- Health warnings.

- [ ] **Step 2: Run cross-check ecosystem test**

Run:

```bash
cd prototypes/card-battle-sim
python3 ecosystem_test.py 500 500
```

Record the same values as Step 1.

- [ ] **Step 3: Apply decision rules**

Use this decision table:

```text
PASS:
- All faction overall rates are 45%-55% in both runs.
- All mirror first-player rates are <=65%.
- France first-player vs Russia is <=65% in both runs.
- PacingRisk is <=0.30 in both runs.
- No matchup average exceeds 21 turns in either run.

TUNE:
- Any faction overall rate is below 45% or above 55%.
- Any mirror first-player rate is above 65%.
- France first-player vs Russia is above 65%.
- PacingRisk is above 0.30.
- Any matchup average exceeds 21 turns.
```

If result is PASS, skip Task 5 and continue to Task 6.

If result is TUNE, continue to Task 5.

## Task 5: Apply Bounded Balance Tuning If Needed

**Files:**

- Modify: `prototypes/card-battle-sim/cards.py`
- Modify: `prototypes/card-battle-sim/test_rule_tuning.py`

Apply one tuning step at a time. After each step, run:

```bash
cd prototypes/card-battle-sim
python3 -m unittest test_rule_tuning.py
python3 ecosystem_test.py 500 0
python3 ecosystem_test.py 500 500
```

### Tuning Step A: Prussia Overall Above 55%

Use this if Prussia overall is above 55% in either ecosystem run.

Change `沙恩霍斯特参谋部` cost from 2 to 3 in `cards.py`:

```python
    deck.append(Card("沙恩霍斯特参谋部", 3, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "draw1_buff_target_INF+1+1"))
```

Update `test_expansion_event_cards_use_existing_effects` in `test_rule_tuning.py`:

```python
                "沙恩霍斯特参谋部": (3, "draw1_buff_target_INF+1+1"),
```

Commit after tests pass:

```bash
git add prototypes/card-battle-sim/cards.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "balance: slow prussian staff office"
```

### Tuning Step B: Prussia Still Above 55%

Use this only if Prussia remains above 55% in either ecosystem run after Step A.

Remove `沙恩霍斯特参谋部` from the official Prussia deck and restore one standard Prussian unit to keep the deck at 33 cards.

Delete this card from `build_prussia_deck()`:

```python
    deck.append(Card("沙恩霍斯特参谋部", 3, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "draw1_buff_target_INF+1+1"))
```

Add one `西里西亚国民军` before the Prussian event cards:

```python
    deck.append(Card("西里西亚国民军", 2, 2, 3, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.MAIN, ["结阵"]))
```

Update `test_faction_event_packages_are_present` by removing `"沙恩霍斯特参谋部"` from the Prussia expected event list.

Update `test_expansion_event_cards_use_existing_effects` by removing the Prussia `"沙恩霍斯特参谋部"` entry. Leave the Prussia expected dictionary as:

```python
            Faction.PRUSSIA: {},
```

Commit after tests pass:

```bash
git add prototypes/card-battle-sim/cards.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "balance: remove prussian staff expansion event"
```

### Tuning Step C: France Falls Below 45%

Use this if France is below 45% in either ecosystem run after Step A or Step B.

Change `军团传令` cost from 3 to 2 in `cards.py`:

```python
    deck.append(Card("军团传令", 2, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, [], CardType.EVENT, "advance_friendly_one_no_attack"))
```

Update `test_expansion_event_cards_use_existing_effects`:

```python
                "军团传令": (2, "advance_friendly_one_no_attack"),
```

Commit after tests pass:

```bash
git add prototypes/card-battle-sim/cards.py prototypes/card-battle-sim/test_rule_tuning.py
git commit -m "balance: restore french command relay tempo"
```

Stop after these three bounded tuning steps. If the game still fails acceptance, report the exact failing metrics and do not invent additional changes.

## Task 6: Document Turn 18 Pressure Timing

**Files:**

- Modify: `docs/superpowers/specs/2026-05-06-napoleon-v02-v04-product-design.md`
- Modify: `prototypes/card-battle-sim/README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Update product design spec**

In `docs/superpowers/specs/2026-05-06-napoleon-v02-v04-product-design.md`, replace:

```markdown
From turn 15 onward, each full round enters a decision phase called Operational Pressure.
```

with:

```markdown
From turn 18 onward, each full round enters a decision phase called Operational Pressure. The original design target was turn 15, but the v0.2 implementation uses turn 18 as the tuned value to preserve early- and midgame faction balance.
```

Replace:

```markdown
- Starting at turn 15, after both players have acted, check whether each player damaged the opposing HQ during that round.
```

with:

```markdown
- Starting at turn 18, after both players have acted, check whether each player damaged the opposing HQ during that round.
```

- [ ] **Step 2: Update README baseline**

In `prototypes/card-battle-sim/README.md`, update the current v0.2 baseline block to include:

```markdown
- 新机制：作战压力（turn 18+，未造成 HQ 伤害的一方 HQ -1）、突破奖励（清线后首次 HQ 直击 +1）
```

Replace old balance lines with the final values from Task 4 or Task 5. Use the exact percentages printed by the final `500 0` and `500 500` runs.

- [ ] **Step 3: Update AGENTS baseline**

In `AGENTS.md`, update Current State with:

```markdown
- v0.2 pacing mechanics: Operational Pressure from turn 18 and Breakthrough Reward
```

Update the balance baseline and known issues with the final values from Task 4 or Task 5.

- [ ] **Step 4: Commit docs**

Run:

```bash
git add docs/superpowers/specs/2026-05-06-napoleon-v02-v04-product-design.md prototypes/card-battle-sim/README.md AGENTS.md
git commit -m "docs: record v0.2 pressure timing and balance"
```

## Task 7: Final Verification

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

- [ ] **Step 2: Run primary ecosystem test**

Run:

```bash
cd prototypes/card-battle-sim
python3 ecosystem_test.py 500 0
```

Expected:

- All faction overall rates are 45%-55%.
- All mirror first-player rates are <=65%.
- France first-player vs Russia is <=65%.
- PacingRisk is <=0.30.
- No matchup average exceeds 21 turns.
- Health assessment does not hide any failing 45%-55% condition behind a green verdict.

- [ ] **Step 3: Run cross-check ecosystem test**

Run:

```bash
cd prototypes/card-battle-sim
python3 ecosystem_test.py 500 500
```

Expected:

- Same acceptance conditions as Step 2.

- [ ] **Step 4: Regenerate default replay**

Run:

```bash
cd prototypes/card-battle-sim
python3 export_match.py FRANCE RUSSIA 42
```

Expected:

- Command exits 0.
- `match_data.json` is updated.
- Output reports winner, turn count, and timeline node count.

- [ ] **Step 5: Compile check**

Run:

```bash
cd prototypes/card-battle-sim
python3 -m py_compile cards.py game.py ai.py combat.py game_state.py export_match.py ecosystem_test.py generate_pdf.py
```

Expected:

- Command exits 0 with no output.

- [ ] **Step 6: Commit regenerated replay if changed**

Run:

```bash
git add prototypes/card-battle-sim/match_data.json
git commit -m "data: refresh replay after v0.2 pressure fix"
```

If `git status --short prototypes/card-battle-sim/match_data.json` shows no change, do not create an empty commit.

- [ ] **Step 7: Final report**

Report these facts in plain text:

```text
Operational Pressure direction fixed: yes/no, with unit test count.
Operational Pressure start turn: 18, documented in spec/README/AGENTS.
Unit tests: include exact unittest result.
Primary balance 500/0: include overall faction rates, France P1 vs Russia, PacingRisk, and health warnings.
Cross-check balance 500/500: include overall faction rates, France P1 vs Russia, PacingRisk, and health warnings.
Decision: PASS or NEEDS MORE TUNING according to Task 4 decision rules.
Commits: list commit hashes created during this plan.
```
