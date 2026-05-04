"""
实验 4：后手补偿机制对先手优势的影响

发现的问题：镜像对决（法 vs 法）先手胜率 62%，先手优势偏大
（健康 CCG 应在 50-55% 之间）

测试三种补偿方案：
A. 后手多抽 1 张（当前默认）
B. 后手多抽 2 张
C. 后手起手军令 +1
D. A + C 组合
"""

import statistics
from cards import Faction
from game import play_one_game
import game


def test_compensation(scheme_name: str, extra_cards: int, extra_orders: int, n: int = 200):
    """改一下 game.py 里的常量，跑测试"""
    # 这里直接 monkey-patch 起手补偿
    import game as g
    
    # 保存原值
    orig_draw = g.STARTING_HAND_SIZE
    orig_orders = g.INITIAL_ORDERS
    
    # 通过修改 play_one_game 来补偿后手
    # 简单办法：runtime 改常量
    
    # 跑镜像对决（剔除阵营因素）
    france_p1_wins = 0
    prussia_p1_wins = 0
    
    for i in range(n):
        # 默认 P2（后手）多抽 1 张已经在 game.py 里
        # 我们这里要再加：extra_cards 张和 extra_orders 军令
        result = play_with_compensation(
            Faction.FRANCE, Faction.FRANCE, 
            seed=i, p2_extra_cards=extra_cards, p2_extra_orders=extra_orders
        )
        if result.winner == 0:
            france_p1_wins += 1
        
        result = play_with_compensation(
            Faction.PRUSSIA, Faction.PRUSSIA,
            seed=i + 10000, p2_extra_cards=extra_cards, p2_extra_orders=extra_orders
        )
        if result.winner == 0:
            prussia_p1_wins += 1
    
    avg_p1_wr = (france_p1_wins + prussia_p1_wins) / (2 * n)
    print(f"  方案 {scheme_name}: P1 镜像胜率 = {avg_p1_wr*100:.1f}% "
          f"(法镜像 {france_p1_wins/n*100:.1f}%, 普镜像 {prussia_p1_wins/n*100:.1f}%)")
    return avg_p1_wr


def play_with_compensation(p1_faction, p2_faction, seed, p2_extra_cards=0, p2_extra_orders=0):
    """play_one_game 的修改版，支持额外的后手补偿"""
    import random
    from cards import build_france_deck, build_prussia_deck
    from game_state import Player, Battlefield
    from game import play_turn, GameResult, STARTING_HQ_HP, STARTING_HAND_SIZE, INITIAL_ORDERS, MAX_TURNS, ORDERS_GROWTH_PER_TURN, MAX_ORDERS
    
    random.seed(seed)
    
    p1 = Player(name=f"P1-{p1_faction.value}", faction=p1_faction,
                deck=build_france_deck() if p1_faction == Faction.FRANCE else build_prussia_deck(),
                hq_hp=STARTING_HQ_HP)
    p2 = Player(name=f"P2-{p2_faction.value}", faction=p2_faction,
                deck=build_france_deck() if p2_faction == Faction.FRANCE else build_prussia_deck(),
                hq_hp=STARTING_HQ_HP)
    
    p1.shuffle_deck()
    p2.shuffle_deck()
    p1.draw(STARTING_HAND_SIZE)
    p2.draw(STARTING_HAND_SIZE)
    
    p1.max_orders = INITIAL_ORDERS
    p1.current_orders = INITIAL_ORDERS
    p2.max_orders = INITIAL_ORDERS + p2_extra_orders
    p2.current_orders = INITIAL_ORDERS + p2_extra_orders
    
    # 后手补偿：多抽 1 + extra
    p2.draw(1 + p2_extra_cards)
    
    battlefield = Battlefield()
    p1_units = 0
    p2_units = 0
    
    for turn in range(1, MAX_TURNS + 1):
        s = play_turn(p1, p2, battlefield, 0, turn, None)
        p1_units += s["units_played"]
        if p2.hq_hp <= 0:
            return GameResult(winner=0, turns=turn, p1_hq_remaining=p1.hq_hp,
                              p2_hq_remaining=p2.hq_hp, p1_units_played=p1_units,
                              p2_units_played=p2_units, end_reason="P2 HQ")
        s = play_turn(p2, p1, battlefield, 1, turn, None)
        p2_units += s["units_played"]
        if p1.hq_hp <= 0:
            return GameResult(winner=1, turns=turn, p1_hq_remaining=p1.hq_hp,
                              p2_hq_remaining=p2.hq_hp, p1_units_played=p1_units,
                              p2_units_played=p2_units, end_reason="P1 HQ")
    
    winner = 0 if p1.hq_hp > p2.hq_hp else (1 if p2.hq_hp > p1.hq_hp else -1)
    return GameResult(winner=winner, turns=MAX_TURNS, p1_hq_remaining=p1.hq_hp,
                      p2_hq_remaining=p2.hq_hp, p1_units_played=p1_units,
                      p2_units_played=p2_units, end_reason="超时")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("实验 4：后手补偿方案测试（镜像对决，n=200）")
    print("="*60)
    print("  目标：先手胜率回到 50-55% 之间\n")
    
    test_compensation("A: 后手 +1 牌（当前）", extra_cards=0, extra_orders=0)
    test_compensation("B: 后手 +2 牌", extra_cards=1, extra_orders=0)
    test_compensation("C: 后手 +1 军令", extra_cards=0, extra_orders=1)
    test_compensation("D: 后手 +1 牌 +1 军令", extra_cards=1, extra_orders=1)
    test_compensation("E: 后手 +2 牌 +1 军令", extra_cards=2, extra_orders=1)
    
    print("\n  解读：")
    print("  - 选择让先手胜率最接近 50% 的方案")
    print("  - 但不要过度补偿（< 45% 会导致后手反而占优）")
