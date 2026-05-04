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


def snapshot_battlefield(p1: Player, p2: Player, bf: Battlefield) -> dict:
    """把当前战场状态序列化为 dict"""
    def unit_to_dict(u: BattleUnit) -> dict:
        return {
            "name": u.card.name,
            "type": u.card.unit_type.value,
            "attack": u.card.attack,
            "current_hp": u.current_hp,
            "max_hp": u.card.health,
            "cost": u.card.cost,
            "slot": u.slot,
            "keywords": list(u.card.keywords),
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
            "rear": [unit_to_dict(u) for u in bf.p1_rear],
            "main": [unit_to_dict(u) for u in bf.p1_main],
            "skirmish": [unit_to_dict(u) for u in bf.p1_skirmish],
        },
        "p2": {
            "name": p2.name,
            "faction": p2.faction.value,
            "hq_hp": p2.hq_hp,
            "orders": f"{p2.current_orders}/{p2.max_orders}",
            "hand_size": len(p2.hand),
            "deck_size": len(p2.deck),
            "discard_size": len(p2.discard_pile),
            "rear": [unit_to_dict(u) for u in bf.p2_rear],
            "main": [unit_to_dict(u) for u in bf.p2_main],
            "skirmish": [unit_to_dict(u) for u in bf.p2_skirmish],
        },
    }


def play_and_export(p1_faction: Faction, p2_faction: Faction, seed: int) -> dict:
    """跑一局，返回完整的播放数据"""
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
    
    # 收集每一步快照
    timeline = []
    
    # 初始状态
    timeline.append({
        "turn": 0,
        "active_player": None,
        "log": ["对局开始"],
        "state": snapshot_battlefield(p1, p2, battlefield),
    })
    
    winner = -1
    end_reason = "超时"
    final_turn = MAX_TURNS
    
    for turn in range(1, MAX_TURNS + 1):
        # P1 回合
        log = []
        play_turn(p1, p2, battlefield, 0, turn, log)
        timeline.append({
            "turn": turn,
            "active_player": 0,
            "active_name": p1.name,
            "log": log,
            "state": snapshot_battlefield(p1, p2, battlefield),
        })
        
        if p2.hq_hp <= 0:
            winner = 0
            end_reason = "P2 HQ 摧毁"
            final_turn = turn
            break
        
        # P2 回合
        log = []
        play_turn(p2, p1, battlefield, 1, turn, log)
        timeline.append({
            "turn": turn,
            "active_player": 1,
            "active_name": p2.name,
            "log": log,
            "state": snapshot_battlefield(p1, p2, battlefield),
        })
        
        if p1.hq_hp <= 0:
            winner = 1
            end_reason = "P1 HQ 摧毁"
            final_turn = turn
            break
    
    return {
        "meta": {
            "p1_faction": p1_faction.value,
            "p2_faction": p2_faction.value,
            "seed": seed,
            "winner": winner,
            "winner_name": ["P1 法兰西", "P2 普鲁士", "P2 俄罗斯",
                           "平局"][winner if winner >= 0 else 3],
            "final_turn": final_turn,
            "end_reason": end_reason,
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
