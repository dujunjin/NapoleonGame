"""
对局可视化导出器

修改 game.py 的对局循环，把每一步的战场快照导出成 JSON。
然后 HTML 可视化页面读取 JSON，逐步播放整局对战。
"""

import json
import random
import sys
from dataclasses import asdict
from cards import Faction, DECK_BUILDERS, Line
from game_state import Player, Battlefield, BattleUnit
from game import (
    play_turn, GameResult,
    STARTING_HQ_HP, STARTING_HAND_SIZE, SECOND_PLAYER_BONUS_DRAW,
    INITIAL_ORDERS, MAX_TURNS
)


SITUATION_NAMES = {
    "dense_fog": "浓雾", "mud": "泥泞",
    "cannon_smoke": "炮烟", "stable_supply": "补给线稳定",
}


def skirmish_state_label(bf: Battlefield) -> str:
    """Return a human-readable skirmish state label for the battlefield."""
    p1 = len(bf.p1_skirmish)
    p2 = len(bf.p2_skirmish)
    if p1 == 0 and p2 == 0:
        return "未接敌"
    if p1 > 0 and p2 == 0:
        return "我方压制"
    if p1 == 0 and p2 > 0:
        return "敌方压制"
    return "交战"


def estimate_exported_hq_threat(attacker_units: list, defender_main: list, defender_skirmish: list) -> int:
    """Estimate total attack power that could hit HQ if defenders are cleared."""
    if defender_main or defender_skirmish:
        return 0
    total = 0
    for unit in attacker_units:
        if unit.current_line.value == "散兵线" or "远程" in unit.card.keywords:
            total += max(0, unit.card.attack)
    return total


def snapshot_battlefield(p1: Player, p2: Player, bf: Battlefield) -> dict:
    """把当前战场状态序列化为 dict"""
    def unit_uid(owner: str, line: Line, u: BattleUnit) -> str:
        return f"{owner}|{line.value}|{u.slot}|{u.card.name}"

    def unit_to_dict(owner: str, line: Line, u: BattleUnit) -> dict:
        return {
            "uid": unit_uid(owner, line, u),
            "name": u.card.name,
            "type": u.card.unit_type.value,
            "attack": u.card.attack,
            "current_hp": u.current_hp,
            "max_hp": u.card.health,
            "cost": u.card.cost,
            "slot": u.slot,
            "keywords": list(u.card.keywords),
            "is_shaken": u.is_shaken,
            "can_act": u.can_act,
            "has_acted_this_turn": u.has_acted_this_turn,
            "deployed_this_turn": u.deployed_this_turn,
        }
    
    return {
        "p1": {
            "name": p1.name,
            "faction": p1.faction.value,
            "hq_hp": p1.hq_hp,
            "orders": f"{p1.current_orders}/{p1.max_orders}",
            "hand_size": len(p1.hand),
            "deck_size": len(p1.deck),
            "discard_size": len(p1.discard_pile),
            "rear": [unit_to_dict("P1", Line.REAR, u) for u in bf.p1_rear],
            "main": [unit_to_dict("P1", Line.MAIN, u) for u in bf.p1_main],
            "skirmish": [unit_to_dict("P1", Line.SKIRMISH, u) for u in bf.p1_skirmish],
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
        },
        "p2": {
            "name": p2.name,
            "faction": p2.faction.value,
            "hq_hp": p2.hq_hp,
            "orders": f"{p2.current_orders}/{p2.max_orders}",
            "hand_size": len(p2.hand),
            "deck_size": len(p2.deck),
            "discard_size": len(p2.discard_pile),
            "rear": [unit_to_dict("P2", Line.REAR, u) for u in bf.p2_rear],
            "main": [unit_to_dict("P2", Line.MAIN, u) for u in bf.p2_main],
            "skirmish": [unit_to_dict("P2", Line.SKIRMISH, u) for u in bf.p2_skirmish],
            "commander": {
                "id": p2.commander_id,
                "name": p2.commander_name,
                "used": p2.commander_used,
                "use_turn": p2.commander_use_turn,
            },
            "objective": {
                "id": p2.objective_id,
                "name": p2.objective_name,
                "completed": p2.objective_completed,
                "completed_turn": p2.objective_completed_turn,
                "reward_pending": p2.objective_reward_pending,
            },
        },
        "ui_summary": {
            "skirmish_state": skirmish_state_label(bf),
            "p1_hq_threat": estimate_exported_hq_threat(
                bf.p1_rear + bf.p1_main + bf.p1_skirmish,
                bf.p2_main, bf.p2_skirmish),
            "p2_hq_threat": estimate_exported_hq_threat(
                bf.p2_rear + bf.p2_main + bf.p2_skirmish,
                bf.p1_main, bf.p1_skirmish),
        },
        # v0.5 Battlefield Situation metadata
        "battlefield_situation": (
            {
                "id": bf.current_situation_id,
                "name": SITUATION_NAMES.get(bf.current_situation_id, bf.current_situation_id),
                "started_turn": bf.current_situation_started_turn,
            }
            if bf.current_situation_id else None
        ),
    }


def _enrich_event_step(step: dict) -> None:
    """Parse event log to extract event card name and effect text."""
    for line in reversed(step.get("log", [])):
        text = line.strip()
        if "打出事件卡【" in text:
            card = text.split("打出事件卡【", 1)[1].split("】", 1)[0]
            effect = text.split("→", 1)[1].strip() if "→" in text else ""
            step["event_card"] = card
            step["event_effect_text"] = effect
            return


def _enrich_commander_reaction(step: dict) -> None:
    """Parse log for commander reaction markers (⚜) and attach to step."""
    for line in step.get("log", []):
        if "⚜" in line:
            step["commander_reaction"] = line.strip()
            return
    step["commander_reaction"] = None


def _enrich_damage_modifiers(step: dict) -> None:
    """Propagate damage_modifiers from attack_event to step level for viewer consumption."""
    ae = step.get("attack_event")
    if ae and "damage_modifiers" in ae:
        step["damage_modifiers"] = ae["damage_modifiers"]


def play_and_export(p1_faction: Faction, p2_faction: Faction, seed: int) -> dict:
    """跑一局，返回完整的播放数据（逐动作时间轴）"""
    random.seed(seed)

    p1 = Player(name=f"P1-{p1_faction.value}", faction=p1_faction,
                deck=DECK_BUILDERS[p1_faction](), hq_hp=STARTING_HQ_HP)
    p2 = Player(name=f"P2-{p2_faction.value}", faction=p2_faction,
                deck=DECK_BUILDERS[p2_faction](), hq_hp=STARTING_HQ_HP)

    p1.shuffle_deck()
    p2.shuffle_deck()
    p1.draw(STARTING_HAND_SIZE)
    p2.draw(STARTING_HAND_SIZE)
    p1.max_orders = INITIAL_ORDERS
    p1.current_orders = INITIAL_ORDERS
    p2.max_orders = INITIAL_ORDERS
    p2.current_orders = INITIAL_ORDERS
    p2.draw(SECOND_PLAYER_BONUS_DRAW)

    battlefield = Battlefield()
    from game import initialize_command_layer
    initialize_command_layer(p1, p2, seed)

    # 收集每一步快照（逐动作）
    timeline = []

    # 初始状态
    timeline.append({
        "turn": 0,
        "active_player": None,
        "action": "start",
        "log": ["对局开始"],
        "state": snapshot_battlefield(p1, p2, battlefield),
    })

    winner = -1
    end_reason = "超时"
    final_turn = MAX_TURNS

    for turn in range(1, MAX_TURNS + 1):
        # P1 回合
        log = []
        sub_steps = []
        play_turn(p1, p2, battlefield, 0, turn, log,
                  sub_steps=sub_steps, snapshot_fn=snapshot_battlefield)

        # 将子步骤展开为时间轴节点
        for step in sub_steps:
            step["turn"] = turn
            step["active_player"] = 0
            step["active_name"] = p1.name
            timeline.append(step)

        # P2 回合
        log = []
        sub_steps = []
        play_turn(p2, p1, battlefield, 1, turn, log,
                  sub_steps=sub_steps, snapshot_fn=snapshot_battlefield)

        for step in sub_steps:
            step["turn"] = turn
            step["active_player"] = 1
            step["active_name"] = p2.name
            timeline.append(step)

        # 胜负在完整轮结束后统一结算（与 game.py play_one_game 一致）
        if p1.hq_hp <= 0 or p2.hq_hp <= 0:
            if p1.hq_hp > p2.hq_hp:
                winner = 0
                end_reason = "P2 HQ 摧毁"
            elif p2.hq_hp > p1.hq_hp:
                winner = 1
                end_reason = "P1 HQ 摧毁"
            else:
                winner = -1
                end_reason = "双方 HQ 同时摧毁"
            final_turn = turn
            break

    # 超时判定：比较 HQ 剩余血量（与 game.py 一致）
    if winner == -1 and final_turn >= MAX_TURNS:
        if p1.hq_hp > p2.hq_hp:
            winner = 0
            end_reason = f"倒计时结束，HQ血量判定 (P1:{p1.hq_hp} vs P2:{p2.hq_hp})"
        elif p2.hq_hp > p1.hq_hp:
            winner = 1
            end_reason = f"倒计时结束，HQ血量判定 (P1:{p1.hq_hp} vs P2:{p2.hq_hp})"
        else:
            end_reason = f"倒计时结束，平局 (P1:{p1.hq_hp} vs P2:{p2.hq_hp})"

    if winner == 0:
        winner_name = f"P1 {p1_faction.value}"
    elif winner == 1:
        winner_name = f"P2 {p2_faction.value}"
    else:
        winner_name = "超时/平局"

    # Assign stable action_id and enrich event steps with card metadata
    for idx, step in enumerate(timeline):
        step["action_id"] = idx
        if step["action"] == "event":
            _enrich_event_step(step)
        _enrich_commander_reaction(step)
        _enrich_damage_modifiers(step)

    return {
        "meta": {
            "p1_faction": p1_faction.value,
            "p2_faction": p2_faction.value,
            "seed": seed,
            "winner": winner,
            "winner_name": winner_name,
            "starting_hq_hp": STARTING_HQ_HP,
            "final_turn": final_turn,
            "end_reason": end_reason,
            "p1_commander": p1.commander_name,
            "p2_commander": p2.commander_name,
            "p1_objective": p1.objective_name,
            "p2_objective": p2.objective_name,
            "p1_objective_completed": p1.objective_completed,
            "p2_objective_completed": p2.objective_completed,
            "trigger_fire_counts": {},
            "trigger_avg_impact": {},
            "sequence_trigger_satisfaction_rate": 0.0,
            "sub_faction_tag_deck_presence": {},
            "same_line_threshold_trigger_count": 0,
            "trigger_first_fire_turn": {},
            "new_card_play_counts": {},
        },
        "timeline": timeline,
    }


if __name__ == "__main__":
    # 默认导出一局：法兰西 vs 俄罗斯
    p1_arg = sys.argv[1] if len(sys.argv) > 1 else "FRANCE"
    p2_arg = sys.argv[2] if len(sys.argv) > 2 else "RUSSIA"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 42
    
    p1_f = Faction[p1_arg]
    p2_f = Faction[p2_arg]
    
    print(f"导出对局：{p1_f.value} vs {p2_f.value} (seed={seed})...")
    data = play_and_export(p1_f, p2_f, seed)
    
    # 修正 winner_name（基于实际阵营）
    w = data["meta"]["winner"]
    if w == 0:
        data["meta"]["winner_name"] = f"P1 {p1_f.value}"
    elif w == 1:
        data["meta"]["winner_name"] = f"P2 {p2_f.value}"
    else:
        data["meta"]["winner_name"] = "超时/平局"
    
    output_path = "match_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"导出完成：{output_path}")
    print(f"  对局结果：{data['meta']['winner_name']}")
    print(f"  回合数：{data['meta']['final_turn']}")
    print(f"  时间轴节点：{len(data['timeline'])}")
