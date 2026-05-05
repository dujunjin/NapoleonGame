# NapoleonGame v0.2-v0.4 Product Design

**Status:** Draft for review  
**Date:** 2026-05-06  
**Perspective:** Product design, with input from creative-director, game-designer, and systems-designer agent reviews  
**Current Baseline:** 3 factions, 33 cards each, HQ 14, event expansion complete

## 1. Product Direction

NapoleonGame should move from a rule simulator into a playable Napoleonic battle card experience. The next versions should not chase more cards first. They should make the current core easier to read, faster to resolve, and more expressive.

The player fantasy is:

> I am a Napoleonic battlefield commander. I read the lines, manage pressure, choose when to commit reserves, and use commanders, weather, and logistics to create a local advantage before the enemy does.

The core experience should be:

- Read the battlefield.
- Identify the pressure point.
- Commit limited orders.
- Accept tactical losses.
- Turn one line into a decisive HQ threat.

## 2. Design Pillars

### 2.1 Battleline Pressure Over Single-Card Burst

Wins should come from battlefield pressure, line control, attrition, breakthrough, and HQ exposure. A single card can create a window, but it should not decide the game by itself.

### 2.2 Faction Identity Must Stay Clear

Current identities:

- France: initiative, tempo, breakthrough.
- Prussia: discipline, reform, counterattack.
- Russia: attrition, retreat, depth, sacrifice.

Every new system must reinforce these identities instead of flattening them into generic CCG effects.

### 2.3 Commanders Are Strategic Identity

Commanders should not be normal cards. They should be chosen before battle and define the player's operational style. Their role is to create a strategic bias, not to act as a super-powered event card.

### 2.4 Events Create Battle Stories

Events should feel like military conditions: orders, weather, morale, logistics, terrain, and battlefield confusion. Their purpose is to create memorable situations and tactical timing windows.

### 2.5 Deckbuilding Gives Expression Without Breaking Testability

Deckbuilding should arrive as limited expression first. The game needs an official baseline deck for balance testing, while players gradually gain room to tune style.

## 3. Anti-Pillars

Do not build toward:

- Complex stack-response gameplay.
- High-randomness comedy effects.
- Commander abilities that decide the game alone.
- A campaign mode that becomes a 4X grand strategy map.
- Full freeform deckbuilding before official baseline decks are stable.
- A fourth faction before pacing and commander systems are validated.
- Historical detail that damages readability or pace.

## 4. Version Roadmap

### v0.2: Balance And Pacing Stabilization

Goal: make the current 3-faction game faster and more stable.

Scope:

- Reduce long games.
- Lower France first-player vs Russia from known-risk range to <=65%.
- Add pacing diagnostics.
- Avoid major new systems.

### v0.3: Core Systems Expansion

Goal: add player-facing strategic identity and long-term play structure while staying within the current 3 factions.

Scope:

- Commander system.
- Lightweight campaign mode.
- Event category system.
- Limited deckbuilding.

### v0.4: Fourth Faction Preproduction

Goal: validate a fourth faction direction through a small test package, not a full faction launch.

Scope:

- Fourth faction fantasy and mechanics.
- 10-card probe package.
- 3 commander concepts.
- Balance risk assessment.

Recommended fourth faction probe: Britain.

## 5. v0.2 Design: Balance And Pacing

### 5.1 Current Problem

The latest accepted baseline is healthy enough to continue, but has two known issues:

- France first-player vs Russia remains in known-risk range: 65.8% / 65.2%.
- Several matchups average around 20-21+ turns.

The goal is not to make the game shorter by forcing artificial timeouts. The goal is to make the midgame produce decisive pressure more reliably.

### 5.2 Target Experience

By the midgame, players should feel the battle tightening:

- Lines are under pressure.
- HQ exposure matters.
- Pure defense becomes risky.
- Every turn has a visible consequence.

### 5.3 Recommended Mechanic: Operational Pressure

From turn 15 onward, each full round enters a decision phase called Operational Pressure.

Rules:

- Starting at turn 15, after both players have acted, check whether each player damaged the opposing HQ during that round.
- A player who dealt no HQ damage that round takes 1 HQ pressure damage.
- If both players dealt HQ damage, no pressure damage is dealt.
- If neither player dealt HQ damage, both take 1 HQ pressure damage.
- Pressure damage ignores guard, range, and line state.
- Pressure damage should be logged and shown in the replay viewer.

Player-facing text:

> Supply lines stretch thin. A commander who cannot force pressure suffers operational strain.

Design purpose:

- Discourages indefinite defensive stalls.
- Keeps early game untouched.
- Makes midgame HQ pressure meaningful.
- Gives Russia and Prussia a reason to counter-pressure instead of only absorbing.

Risk:

- If pressure starts too early, France tempo may become stronger.
- Turn 15 is the earliest acceptable trigger for first testing.

### 5.4 Recommended Mechanic: Breakthrough Reward

Breakthrough rewards a player for clearing a contested line and converting that line into HQ pressure.

Rules:

- If a player clears enemy units from a line during their action and still has at least one living unit able to threaten from that line, that line gains a temporary Breakthrough marker.
- The first HQ direct attack from that line during the same turn deals +1 damage.
- Each player can trigger Breakthrough at most once per turn.
- Breakthrough expires at end of turn.
- Breakthrough should be visible in replay history and action summaries.

Design purpose:

- Makes line clearing feel decisive.
- Rewards battlefield control rather than passive stat accumulation.
- Creates a readable reason for HQ damage spikes.

Risk:

- Cavalry and artillery could over-benefit if the trigger is too loose.
- The once-per-turn cap is mandatory for the first version.

### 5.5 Pacing Metrics

v0.2 should track more than overall win rate.

Required metrics:

- Overall faction win rate.
- Matchup first-player win rate.
- Mirror first-player win rate.
- Average turns per matchup.
- Timeout rate.
- Long-game rate: percentage of games above 21 turns.
- First HQ damage turn.
- Lethal turn.
- Unspent orders at end of turn.

Recommended pacing score:

```text
PacingRisk = TimeoutRate * 2 + LongGameRate + max(0, AvgTurns - 20) * 0.1
```

Target:

- PacingRisk <= 0.30.
- Timeout rate <=3%.
- No matchup average above 21 turns.
- Overall average <=20 turns.

### 5.6 v0.2 Acceptance Criteria

- Unit tests pass.
- `ecosystem_test.py 500 0`:
  - France, Prussia, Russia each 45%-55%.
  - Mirror first-player <=65%.
  - France first-player vs Russia <=65%.
- `ecosystem_test.py 500 500` confirms the same range.
- No matchup averages above 21 turns.
- Replay viewer shows Operational Pressure and Breakthrough sources clearly.

## 6. v0.3 Design: Commander System

### 6.1 Product Role

Commanders give players a strategic identity before battle. They should answer:

> How does this army intend to win this battle?

Commanders are not deck cards. They are selected before the match, shown persistently in the UI, and used once per match or as a narrow passive.

### 6.2 Commander Rules

- Each player chooses one commander before battle.
- Commander does not enter the deck.
- Commander does not count toward deck size.
- Commander ability is either once per match or a narrow first-time passive.
- Commander ability cannot directly destroy HQ.
- Commander cannot alter battlefield capacity.
- Commander cannot trigger every turn.
- Used commander abilities are shown as exhausted in UI.

### 6.3 Initial Commander Set

France:

- Napoleon: offensive breakthrough. Once per match, one line's first HQ direct attack this turn deals +1.
- Davout: disciplined corps. Once per match, one infantry or guard gains +0/+2 and Guard.
- Murat: cavalry shock. Once per match, one cavalry may advance one extra step this turn, but cannot receive defensive buffs this turn.

Prussia:

- Blucher: counterattack. Once per match, wounded friendly units gain +1 attack this turn.
- Scharnhorst: reform. First draw or replenishment effect each game looks at one extra card and keeps one.
- Gneisenau: staff coordination. Once per match, cancel one negative weather effect for friendly units during an action.

Russia:

- Kutuzov: strategic withdrawal. Once per match, retreat one friendly unit and restore 1 HQ.
- Bagration: rear guard. Once per match, one unit gains Guard and deals 1 retaliation damage to its next attacker.
- Barclay: scorched earth. Once per match, friendly HQ takes 1 damage and the enemy's most forward unit takes 2 damage.

### 6.4 Commander Acceptance Criteria

- Each faction has 3 selectable commanders.
- AI can use commanders without obvious waste.
- Replay viewer shows commander selection and activation.
- Any commander variant keeps faction overall win rate in 45%-55%.
- Commander impact delta should be 2%-6% versus no-commander baseline.
- No commander exceeds its faction average by more than 5 percentage points unless explicitly marked advanced/high-risk.

## 7. v0.3 Design: Campaign Mode

### 7.1 Product Role

Campaign mode turns isolated battles into a short operational arc. The player should feel that a costly victory matters, but the system should not become a grand strategy game.

### 7.2 Campaign Structure

- 5-7 nodes per campaign.
- 25-45 minute total campaign length.
- Player selects faction and commander at start.
- Each node is either a battle or a strategic choice.
- Final node is a decisive battle.

Node types:

- Battle: standard fight.
- Skirmish: lower HQ, faster fight.
- Supply Depot: recover HQ or remove damage.
- Staff Council: replace 1-3 cards for the next battle.
- Severe Weather: next battle starts with a weather condition.
- Decisive Battle: stronger enemy commander condition, but player may bring one campaign reward.

### 7.3 Campaign Resources

Supply:

- Used to recover HQ, remove temporary damage, or buy a small deck adjustment.

Morale:

- Modified by victory quality.
- High morale may improve opening hand quality.
- Low morale may reduce flexibility but should not create a death spiral.

Veteran Mark:

- Limited unit upgrade marker.
- Maximum 3 active veteran marks.
- No permanent card deletion or permanent runaway scaling in v0.3.

### 7.4 Campaign Acceptance Criteria

- A full campaign can be completed in 25-45 minutes.
- At least 5 nodes exist.
- At least 3 node types exist.
- Each post-battle step offers a meaningful choice.
- Campaign rewards do not push final battle win rate above 60%.
- Campaign log shows nodes, rewards, losses, and final result.

## 8. v0.3 Design: Event Deepening

### 8.1 Product Role

Events should be military conditions, not generic spells. They should help players tell the story of a battle:

- An order arrived at the right time.
- Mud slowed the cavalry.
- A reserve held the line.
- A scorched-earth choice bought time at a cost.

### 8.2 Event Categories

Order:

- Immediate action manipulation: advance, retreat, focus, redeploy.

Weather:

- Temporary or lasting battlefield condition.
- Only one global weather should be active at a time.

Morale:

- Affects wounded units, death triggers, guard, and temporary attack.

Logistics:

- Affects draw, supply, cost, HQ repair, and campaign resources.

Reaction:

- Conditional response to attack, deployment, or HQ damage.
- Keep rare in v0.3 to avoid stack complexity.

### 8.3 Event Constraints

- Event cards should be 20%-25% of a faction deck.
- Weather cards: maximum 2 per deck.
- Direct HQ damage event: maximum 1 per faction and must include cost or condition.
- No event should deal more than 4 unavoidable HQ damage in one turn.
- Draw events should not also provide large permanent stat buffs.
- Full-board low-cost events must be symmetric or short-duration.

## 9. v0.3 Design: Limited Deckbuilding

### 9.1 Product Role

Deckbuilding lets players express strategy without immediately creating an impossible balance space.

### 9.2 Recommended Structure

- Each faction has a 42-card pool.
- Match deck remains 33 cards.
- Official preset decks remain the balance baseline.
- Custom decks are allowed for experimentation but not the first balance commitment.

Deck constraints:

- Unit cards: at least 24.
- Event cards: at most 9.
- 1-2 cost cards: at least 8.
- 5+ cost cards: at most 6.
- Guard cards: at most 5.
- Weather cards: at most 2.
- Direct HQ damage events: at most 1.
- Same-name copies:
  - Common units: up to 3.
  - Elite, guard, commander-related events: up to 2.
  - Unique historical people/events: 1.

### 9.3 UX Requirements

Deckbuilding UI should show:

- Cost curve.
- Unit/event ratio.
- Keyword distribution.
- Event category count.
- Illegal deck reasons.
- Commander synergy tags.

Each faction should ship with 3 presets:

- Standard.
- Aggressive.
- Defensive.

## 10. v0.4 Design: Fourth Faction Probe

### 10.1 Agent Recommendation Split

Creative and gameplay review recommend Britain because it has stronger product identity.

Systems review recommends Austria because it is lower-risk and easier to balance.

Product decision:

> Use Britain as the v0.4 probe, but do not immediately build a full 33-card faction.

Reasoning:

- Britain has stronger player-facing identity: Wellington, Nelson, naval support, disciplined fire, coalition warfare.
- Britain expands the fantasy more than another continental line-infantry faction.
- Systems risk is real, so the first step should be a 10-card probe plus 3 commanders.

### 10.2 Britain Player Fantasy

Britain plays like a disciplined expeditionary force:

- Hold the line.
- Absorb the charge.
- Use fire discipline and supply to outlast pressure.
- Counterattack after the enemy's offensive weakens.

### 10.3 Britain Core Mechanics

Discipline:

- If a unit with Discipline did not advance this turn, the first damage it takes this round is reduced by 1.
- If it survives that damage, its next attack gets +1.
- Each unit can trigger Discipline once per round.

Line Volley:

- If two British infantry occupy the same line, the first attack from that line gets +1.

Naval Supply:

- Higher-cost logistics events that restore HQ, draw, or reduce cost of a later support card.
- Naval Supply must not become a separate naval battlefield.

Coalition:

- Low-cost allied support units from Portugal, Hanover, or the Netherlands.
- Coalition units fill lines or support effects; they should not become the main power source.

Reverse Slope:

- Defensive event or commander effect.
- A line ignores the first artillery damage it would take this turn.

### 10.4 Britain Commanders

Wellington:

- Defensive line commander.
- Once per match, one line gains Reverse Slope and British infantry on that line gain +1 on their next counterattack.

Nelson:

- Naval logistics commander.
- Once per match, draw 1 and restore 1 HQ. If HQ is 7 or lower, the next logistics event costs 1 less.

Moore:

- Mobile withdrawal commander.
- Once per match, retreat one infantry and deploy a light infantry token or low-cost unit to an adjacent line.

### 10.5 Britain Risks

- Too much defense could worsen long-game pacing.
- Naval Supply could become a new economy system too early.
- Discipline may make France too weak if it directly counters tempo too hard.
- Coalition could blur faction identity if it becomes a generic tool pool.

### 10.6 v0.4 Probe Acceptance Criteria

- Britain probe has 10 test cards and 3 commanders.
- Britain mechanics are visible in replay.
- Britain vs France does not push France first-player above 65%.
- Britain-related matchups average <=20 turns.
- Britain does not reduce any existing faction's overall win rate below 45%.
- Probe decision is made before building a full 33-card deck:
  - Continue Britain.
  - Switch to Austria.
  - Redesign Britain mechanics.

## 11. Production Split

Recommended implementation order:

1. v0.2 pacing metrics.
2. v0.2 Operational Pressure.
3. v0.2 Breakthrough Reward.
4. v0.2 balance pass and replay labels.
5. v0.3 commander system, one commander per faction first.
6. v0.3 full commander roster.
7. v0.3 event category metadata.
8. v0.3 campaign prototype.
9. v0.3 limited deckbuilding validator.
10. v0.4 Britain probe.

Do not implement campaign, deckbuilding, and fourth faction in the same pass.

## 12. Review Questions

Review these decisions before writing implementation plans:

- Should v0.2 use both Operational Pressure and Breakthrough Reward, or test one at a time?
- Should commanders launch with 1 per faction first, or all 3 per faction?
- Should campaign mode be 3-5 nodes for prototype speed or 5-7 nodes for closer product feel?
- Should v0.4 commit to Britain as the fourth faction probe, or run Britain vs Austria as competing paper designs first?

