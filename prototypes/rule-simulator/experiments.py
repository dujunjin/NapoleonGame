"""
对照实验：测试关键参数对游戏节奏的影响

实验 1：交换先后手（验证规则对称性）
实验 2：不同 HQ 血量（找出最佳节奏点）
实验 3：先后手补偿对胜率的影响
"""

import statistics
from cards import Faction
from game import play_one_game
import game


def run_quick(n: int, p1: Faction, p2: Faction, seed_offset: int = 0):
    """快速跑 n 局，返回核心指标"""
    results = []
    for i in range(n):
        r = play_one_game(p1_faction=p1, p2_faction=p2, verbose=False, seed=i + seed_offset)
        results.append(r)
    
    p1_winrate = sum(1 for r in results if r.winner == 0) / n
    avg_turns = statistics.mean(r.turns for r in results)
    return p1_winrate, avg_turns


def experiment_1_symmetry():
    """实验 1：先后手交换"""
    print("\n" + "="*60)
    print("实验 1：阵营对称性（哪一方先手会赢）")
    print("="*60)
    
    # 法兰西先手
    p1_wr, avg = run_quick(100, Faction.FRANCE, Faction.PRUSSIA, seed_offset=0)
    print(f"  法兰西先手 vs 普鲁士后手: 法兰西胜率 {p1_wr*100:.1f}%, 平均 {avg:.1f} 回合")
    
    # 普鲁士先手
    p1_wr, avg = run_quick(100, Faction.PRUSSIA, Faction.FRANCE, seed_offset=1000)
    print(f"  普鲁士先手 vs 法兰西后手: 普鲁士胜率 {p1_wr*100:.1f}%, 平均 {avg:.1f} 回合")
    
    print("\n  解读：")
    print("  - 如果两个'先手胜率'都 >55%，说明先手优势严重")
    print("  - 如果两个'先手胜率'差距 <8%，说明阵营基本平衡")
    
    # 法 vs 法（镜像）
    p1_wr, avg = run_quick(100, Faction.FRANCE, Faction.FRANCE, seed_offset=2000)
    print(f"\n  镜像对决（法 vs 法）：先手胜率 {p1_wr*100:.1f}%, 平均 {avg:.1f} 回合")
    print("  → 这个数字直接反映先手优势（剔除阵营因素）")
    
    p1_wr2, avg2 = run_quick(100, Faction.PRUSSIA, Faction.PRUSSIA, seed_offset=3000)
    print(f"  镜像对决（普 vs 普）：先手胜率 {p1_wr2*100:.1f}%, 平均 {avg2:.1f} 回合")


def experiment_2_hq_hp():
    """实验 2：HQ 血量对节奏的影响"""
    print("\n" + "="*60)
    print("实验 2：HQ 起始血量 vs 平均回合数")
    print("="*60)
    print(f"  {'HQ血量':<8} {'平均回合':<10} {'P1胜率':<10} {'最长局'}")
    
    original_hp = game.STARTING_HQ_HP
    
    for hp in [15, 20, 25, 30, 35]:
        game.STARTING_HQ_HP = hp
        results = [play_one_game(verbose=False, seed=i) for i in range(50)]
        avg_t = statistics.mean(r.turns for r in results)
        p1_wr = sum(1 for r in results if r.winner == 0) / 50
        max_t = max(r.turns for r in results)
        timeout_rate = sum(1 for r in results if "超时" in r.end_reason) / 50
        print(f"  {hp:<8} {avg_t:<10.1f} {p1_wr*100:<10.1f}% {max_t}回合 (超时{timeout_rate*100:.0f}%)")
    
    game.STARTING_HQ_HP = original_hp
    print("\n  解读：选择让平均回合落在 10-15 区间的 HQ 血量")


def experiment_3_starting_hand():
    """实验 3：起手手牌数量影响"""
    print("\n" + "="*60)
    print("实验 3：起手手牌数对节奏的影响")
    print("="*60)
    print(f"  {'起手牌':<8} {'平均回合':<10} {'P1胜率':<10}")
    
    original = game.STARTING_HAND_SIZE
    
    for n_cards in [3, 4, 5, 6]:
        game.STARTING_HAND_SIZE = n_cards
        results = [play_one_game(verbose=False, seed=i) for i in range(50)]
        avg_t = statistics.mean(r.turns for r in results)
        p1_wr = sum(1 for r in results if r.winner == 0) / 50
        print(f"  {n_cards:<8} {avg_t:<10.1f} {p1_wr*100:<10.1f}%")
    
    game.STARTING_HAND_SIZE = original


if __name__ == "__main__":
    experiment_1_symmetry()
    experiment_2_hq_hp()
    experiment_3_starting_hand()
