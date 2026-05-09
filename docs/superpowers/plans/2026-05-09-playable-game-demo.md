# Playable Game Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a single-file playable HTML card battle game demo where the player controls one faction against an AI opponent, with full game rules ported from Python to JavaScript.

**Architecture:** Single `game.html` file containing CSS (reusing viewer's Napoleonic visual design), HTML (interactive game board), and JavaScript (card data, game engine, combat system, AI, UI interaction). Player interacts via click: select cards from hand → deploy to slots → advance units → select attackers → select targets. AI takes turn automatically.

**Tech Stack:** HTML5, CSS3, Vanilla JavaScript (no frameworks)

**Scope:** All 3 factions (33 cards each), full keyword system, commander abilities, tactical objectives, simplified trigger system. Player vs AI.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `prototypes/card-battle-sim/game.html` | Create | Complete playable game demo |

---

## Task 1: CSS + HTML Shell + Card Data

Build the complete file with:
- CSS from viewer's epic Napoleonic theme
- HTML structure: title, faction select, game board (HQ + 5 lines), hand area, action bar, status panel
- JS card data: all 33 cards × 3 factions ported from `cards.py`

## Task 2: Game Engine + Combat + AI

Port to JS:
- Game state (Player, Battlefield, BattleUnit)
- Turn loop (draw → deploy → advance → attack → end)
- Combat (damage calc, keywords: 冲锋/结阵/远程/闪避/突破/守卫/齐射/侧翼迂回)
- AI opponent (heuristic from `ai.py`)
- Commander abilities
- Event cards

## Task 3: Interactive UI + Polish

Add player interaction:
- Hand display with card hover/click
- Deploy: click card → click empty rear slot
- Advance: click unit → click advance button
- Attack: click attacker → click legal target
- End turn button
- Phase indicator
- Damage animations, HP bars
- Victory/defeat screen

## Verification

- Load `game.html` in browser
- Select a faction, play a complete match
- Verify all keywords work correctly
- Verify AI makes reasonable moves
- Verify win/loss detection works
