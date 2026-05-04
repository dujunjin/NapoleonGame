# Napoleon Card Tactics

**Status**: In Design  
**Owner**: Game Design  
**Last Updated**: 2026-05-04  

## Overview

Napoleon Card Tactics is a two-player tactical card game about Napoleonic battlefield pressure. Players command national decks, deploy infantry, cavalry, artillery, skirmishers, and guards across three battlefield lines, then spend orders to develop tempo, advance units, and break the enemy HQ.

The current project is engine-independent. The playable rules live in the Python simulator and HTML AI match viewer under `prototypes/card-battle-sim/`. The immediate goal is not engine production; it is validating whether the paper and browser prototype produces readable, interesting, and balanced matches.

## Player Fantasy

The player fantasy is being a Napoleonic field commander under constrained orders: forming lines, committing cavalry at the right moment, deciding when artillery should clear formations or threaten HQ, and accepting national tradeoffs. France should feel elite and aggressive, Prussia disciplined and resilient, and Russia attritional with costly long-game effects.

## Core Rules

The battlefield has three relevant lines per player: rear, main, and skirmish. Cards deploy to a default line, then eligible main-line units can advance into the skirmish line by spending orders. HQ damage generally requires units to establish forward pressure or artillery to have a clear shot.

Each turn currently follows this flow:

1. Draw cards. If hand size is 2 or less, draw 2 cards; otherwise draw 1 card.
2. Restore orders. Orders grow quickly to 6, then grow every other turn until the cap of 10.
3. Deploy cards using orders.
4. Advance selected units from main line to skirmish line.
5. Resolve AI attacks.
6. Check HQ destruction or timeout.

Implemented keywords include charge, formation, volley, ranged, evade, breakthrough, guard, flank maneuver, self-damage, and aura bonuses.

## Formulas

Damage uses unit type and keyword modifiers:

- Cavalry against non-formed infantry doubles damage.
- Cavalry against formed infantry deals reduced damage.
- Artillery gains bonus damage against infantry and guards.
- Ranged artillery does not take counterattack damage.
- Volley adds pre-strike damage.
- Breakthrough overflow damages HQ when the target dies.

Orders start at 2. The current order curve is:

- Below 6: `max_orders += 1` each turn.
- At 6 or above: `max_orders += 1` only on even-numbered turns.
- Cap: 10.

Draw curve:

- `hand_size <= 2`: draw 2.
- Otherwise: draw 1.

## Edge Cases

- A player with an empty deck draws nothing and does not take fatigue damage.
- A full deployment line prevents additional deployment to that line.
- A unit deployed this turn cannot act unless it has charge.
- Ranged artillery can attack HQ only when enemy skirmish and main lines are empty, and it spends 1 extra order for the HQ strike.
- Aura effects currently modify card instances on existing battlefield units. Viewer logs must make these effects understandable because the effect is otherwise easy to miss.

## Dependencies

- Current simulation code: `prototypes/card-battle-sim/game.py`, `combat.py`, `ai.py`, `cards.py`, `game_state.py`.
- Earlier simulator: `prototypes/rule-simulator/`.
- Current viewer: `prototypes/card-battle-sim/viewer.html`.
- Current replay data: `prototypes/card-battle-sim/match_*.json`.
- Printable prototype: `prototypes/card-battle-sim/napoleon_cards.pdf`.
- Research basis: `design/research/napoleon/`.

## Tuning Knobs

- HQ starting HP.
- Starting hand size and second-player compensation.
- Low-hand draw threshold and draw count.
- Order growth slowdown point and maximum orders.
- Ranged artillery HQ strike cost.
- Line capacity.
- Card counts and faction-specific stat lines.
- AI deployment, advance, and target-priority heuristics.

## Acceptance Criteria

- The simulator can export a replay JSON without errors.
- The viewer can load `viewer.html` and `match_data.json` through a local HTTP server.
- Core rule changes have focused regression tests.
- A typical AI match ends without timeout and remains readable in the viewer.
- Human playtest notes can identify whether hand size, order pressure, and line control feel understandable.
