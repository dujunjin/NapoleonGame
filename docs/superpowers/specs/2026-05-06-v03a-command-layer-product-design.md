# NapoleonGame v0.3A Command Layer Product Design

**Status:** Draft for review  
**Date:** 2026-05-06  
**Perspective:** Product design  
**Baseline:** v0.2 accepted balance target: France 48.4%, Prussia 52.4%, Russia 49.2% on `500 0`; cross-check France 47.1%, Prussia 53.3%, Russia 49.5% on `500 500`; PacingRisk <=0.30.

## 1. Goal

v0.3A should improve moment-to-moment game feel without expanding the card pool or adding a fourth faction.

The design goal is to make each match feel more intentional:

- The player starts with a strategic identity.
- The player has a short-term battlefield objective.
- The replay can explain why a key moment mattered.

This version adds two small systems:

- Commander: one selected strategic identity per faction.
- Tactical Objective: one public short-term goal per player.

## 2. Why This Is Next

v0.2 stabilized pace and balance. The next problem is not content quantity; it is decision texture.

Current match flow can still feel like:

1. Draw cards.
2. Deploy best available unit.
3. Advance or attack.
4. Repeat until HQ collapses.

v0.3A should add a layer of intent:

1. I chose this commander, so I am looking for this kind of battle.
2. My objective gives me a short-term reason to contest a specific battlefield pattern.
3. I can read the replay and see when my plan worked or failed.

## 3. Scope

In scope:

- 1 commander per existing faction.
- 5 shared Tactical Objectives.
- Basic AI commander use.
- Basic AI objective pursuit only if it is cheap and obvious.
- Replay/export metadata for commander and objective state.
- Viewer display for commander, objective, completion, and reward source.

Out of scope:

- 3 commanders per faction.
- Commander deckbuilding.
- Commander leveling.
- Campaign mode.
- Limited deckbuilding.
- Fourth faction.
- Reaction events.
- New card pool expansion.

## 4. Design Pillars

### 4.1 Commanders Define Intent, Not Raw Power

Commander abilities should create a timing decision. They should not be always-on stat engines.

### 4.2 Objectives Pull Players Into The Battlefield

Tactical Objectives should reward line control, HQ pressure, unit survival, or sacrifice timing. They should not reward passive stalling.

### 4.3 Replay Must Explain The Plan

If a commander ability or objective reward changes the outcome, the viewer should show it clearly.

### 4.4 Balance Remains The Gate

No system in v0.3A is accepted unless the three-faction balance remains inside the v0.2 acceptance bands.

## 5. Commander System

### 5.1 Product Role

Commanders answer:

> What kind of battle am I trying to fight?

A commander is selected before the match. It does not enter the deck and does not count toward deck size.

### 5.2 Global Commander Rules

- Each player has exactly 1 commander.
- The default commander is selected automatically by faction.
- Commander ability can be used once per match.
- Commander starts unused.
- Commander ability usage is logged.
- Commander ability usage appears in replay timeline.
- Commander abilities do not directly deal unavoidable HQ damage.
- Commander abilities do not change deck size, hand size, max orders, HQ max HP, or battlefield capacity.

### 5.3 Initial Commander Roster

#### France: Napoleon

Fantasy:

Napoleon creates a decisive local attack. The player waits for one line to become exposed, then converts it into HQ pressure.

Ability:

`Imperial Breakthrough`

Rules:

- Once per match.
- Choose one friendly occupied line.
- Until end of current turn, the first HQ direct attack from that line deals +1 damage.
- Does not stack with another commander ability.
- Can stack with v0.2 Breakthrough Reward only if balance tests remain healthy.

Player question:

> Is this the turn where I turn a line advantage into a real HQ threat?

Risk:

- France already has tempo pressure. This ability may push France first-player too high if it stacks too easily with Breakthrough.

Balance fallback:

- If France first-player vs Russia exceeds 65%, Napoleon's bonus applies only if the attacking unit was already on MAIN or SKIRMISH at the start of turn.

#### Prussia: Blucher

Fantasy:

Blucher turns a damaged army into a counterattack. The player wants to survive the first blow and answer hard.

Ability:

`Counterstroke`

Rules:

- Once per match.
- Until end of current turn, each wounded friendly unit gets +1 attack.
- A wounded unit is a unit whose current HP is below max HP.
- Units that become wounded later in the same turn do not gain the bonus retroactively unless they attack after becoming wounded.

Player question:

> Do I cash in my damaged line now before it collapses?

Risk:

- Prussia is currently slightly above the middle of the pack. This must be tuned carefully.

Balance fallback:

- If Prussia overall exceeds 55%, limit the bonus to the first two wounded units that attack this turn.

#### Russia: Kutuzov

Fantasy:

Kutuzov trades space for survival. The player uses withdrawal to deny a bad exchange and keep the army alive.

Ability:

`Strategic Withdrawal`

Rules:

- Once per match.
- Choose one friendly unit not in REAR.
- Move that unit to REAR.
- Heal that unit by 1, capped at max HP.
- Restore friendly HQ by 1.
- The moved unit cannot attack again this turn.

Player question:

> Which unit is worth saving, and can I afford to give up its position?

Risk:

- If too strong, Russia may return to long-game stall patterns.

Balance fallback:

- If Russia games exceed pacing targets, remove the unit heal and keep only HQ +1.

## 6. Tactical Objective System

### 6.1 Product Role

Tactical Objectives create short-term battlefield goals. They should make the player care about more than simply playing the best card each turn.

Each player receives one public objective at match start.

### 6.2 Global Objective Rules

- Each player has exactly 1 active Tactical Objective.
- Objectives are public.
- Objectives are assigned at match start.
- Objective reward can trigger once.
- After completion, objective is marked complete and no replacement is assigned in v0.3A.
- Objective completion is logged.
- Objective reward source appears in replay timeline.
- Objective rewards should be small and immediate.

### 6.3 Objective Assignment

For v0.3A, use deterministic objective assignment from seed and player index.

Requirements:

- Same match seed produces the same objectives.
- P1 and P2 should not receive the same objective if at least two objectives are available.
- Future versions may allow commander-specific objective pools, but v0.3A uses a shared pool.

## 7. Initial Tactical Objectives

### 7.1 Seize The Skirmish Line

Trigger:

- At the end of a player's action, the player has at least one unit in SKIRMISH and the opponent has no unit in SKIRMISH.

Reward:

- Draw 1 card.

Purpose:

- Pulls players into the contested forward space.

Risk:

- If too easy for fast factions, it may become automatic.

Target completion rate:

- 40%-65%.

### 7.2 First Blood On HQ

Trigger:

- The first time the player damages enemy HQ.

Reward:

- Gain +1 current_orders this turn, capped by max_orders.

Purpose:

- Rewards early pressure without increasing long-term economy.

Risk:

- May strengthen France. If France exceeds 55% or France P1 vs Russia exceeds 65%, change reward to draw 1 only if hand size is <=3.

Target completion rate:

- 50%-75%.

### 7.3 Hold The Main Line

Trigger:

- At the end of a full round, the player has at least 2 units in MAIN.

Reward:

- Restore HQ by 1.

Purpose:

- Encourages stable battleline formation.

Risk:

- Could support stalling. It is acceptable only because it completes once.

Target completion rate:

- 35%-60%.

### 7.4 Prepare The Guns

Trigger:

- A friendly ARTILLERY unit starts and ends the player's action alive in REAR.

Reward:

- That player's next artillery attack deals +1 damage.

Purpose:

- Makes rear-line artillery preparation feel like an explicit plan.

Risk:

- May produce too much HQ pressure if artillery can safely chain attacks.

Target completion rate:

- 30%-55%.

### 7.5 Sacrifice For Time

Trigger:

- During a full round, at least one friendly unit dies and the opponent deals no HQ damage that round.

Reward:

- Draw 1 card.

Purpose:

- Gives defensive factions a way to turn losses into tempo without directly healing.

Risk:

- Could reward passive defense if too easy. The no-HQ-damage condition is required.

Target completion rate:

- 30%-55%.

## 8. AI Behavior

### 8.1 Commander AI

AI does not need perfect commander play in v0.3A. It needs to avoid obvious waste.

Napoleon AI:

- Use if at least one friendly unit can perform HQ direct attack this turn.
- Prefer a line that also has Breakthrough Reward.

Blucher AI:

- Use if at least two wounded friendly units can attack this turn.
- Use if one wounded high-attack unit can attack HQ this turn.

Kutuzov AI:

- Use if a non-REAR friendly unit has current HP <=2 and enemy units can attack it next turn.
- Prefer units with Guard, artillery, guard type, or high cost.

### 8.2 Objective AI

AI can remain mostly existing-policy driven. Add only low-risk nudges:

- If objective is Seize The Skirmish Line, value advancing into SKIRMISH slightly higher.
- If objective is First Blood On HQ, value available HQ direct attacks normally; no special forced behavior.
- If objective is Hold The Main Line, do not advance the second MAIN unit out of MAIN unless it creates HQ pressure.
- If objective is Prepare The Guns, avoid advancing artillery out of REAR before objective completes.
- If objective is Sacrifice For Time, no special behavior in v0.3A.

## 9. Replay And Viewer Requirements

Replay export should include:

- P1 commander name.
- P2 commander name.
- Commander used flag.
- Commander use step.
- P1 objective name.
- P2 objective name.
- Objective complete flag.
- Objective completion step.
- Objective reward summary.

Viewer should show:

- Commander in match header or player panel.
- Commander used/unused state.
- Tactical Objective in each player panel.
- Completed objective state.
- Action panel line when a commander is used.
- Action panel line when objective completes.

No advanced animation is required in v0.3A.

## 10. Balance And Test Acceptance

Functional acceptance:

- Unit tests pass.
- Commander can be assigned.
- Commander can be used once.
- Commander cannot be used twice.
- Objective is assigned deterministically.
- Objective completes once.
- Objective reward applies once.
- Replay export contains commander/objective metadata.

Balance acceptance:

- `python3 ecosystem_test.py 500 0`:
  - France, Prussia, Russia each 45%-55%.
  - Mirror first-player <=65%.
  - France first-player vs Russia <=65%.
  - PacingRisk <=0.30.
  - No matchup average >21 turns.
- `python3 ecosystem_test.py 500 500` confirms the same.

Objective quality acceptance:

- Each objective completion rate should be between 30%-75%.
- At least 3 of 5 objectives should complete in 35%-65% of games.
- No objective should correlate with a faction exceeding 55% overall.

Replay acceptance:

- A reviewer can identify commander selection, commander use, objective assignment, objective completion, and reward source from the viewer without reading raw JSON.

## 11. Tuning Rules

Tune in this order:

1. Commander reward magnitude.
2. Objective reward magnitude.
3. Objective trigger strictness.
4. AI objective nudge weight.
5. Existing card stats only if commander/objective tuning cannot solve the issue.

Do not tune:

- HQ HP.
- Deck size.
- Operational Pressure start turn.
- Breakthrough Reward base rule.
- Max turns.

## 12. Implementation Split Recommendation

Plan A: minimal vertical slice.

1. Add commander data model and default commander per faction.
2. Add commander use logic for Napoleon, Blucher, Kutuzov.
3. Add objective data model and deterministic assignment.
4. Implement 5 objective triggers and rewards.
5. Add AI use rules.
6. Add export metadata.
7. Add viewer display.
8. Run unit and ecosystem tests.

Plan B: if scope must be smaller.

1. Add commanders only.
2. Validate balance.
3. Add objectives in a second pass.

Recommended path:

Use Plan A if Claude is executing with tests and balance validation. Use Plan B if the implementation window is short.

