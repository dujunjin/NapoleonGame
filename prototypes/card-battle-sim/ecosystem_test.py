"""
三阵营生态测试

跑全部 6 种对决组合，看是否出现：
- 阵营失衡（某阵营全胜或全败）
- 剪刀石头布（A克B、B克C、C克A 的健康循环）
- 阵营特色是否在数据中体现
"""

import statistics
from cards import Faction
from game import play_one_game


def test_matchup(p1_f: Faction, p2_f: Faction, n: int = 200) -> dict:
    """跑一组对决，返回统计"""
    results = []
    for i in range(n):
        # 用 hash 让不同对决的种子不重复
        seed = hash((p1_f.name, p2_f.name, i)) % 100000
        r = play_one_game(p1_faction=p1_f, p2_faction=p2_f, verbose=False, seed=seed)
        results.append(r)
    
    p1_wins = sum(1 for r in results if r.winner == 0)
    # 软超时：到达 MAX_TURNS 上限 → 倒计时结束判定
    timeouts = sum(1 for r in results if r.end_reason.startswith("倒计时结束") or "超时" in r.end_reason)
    avg_turns = statistics.mean(r.turns for r in results)
    
    return {
        "p1_winrate": p1_wins / n,
        "avg_turns": avg_turns,
        "timeouts": timeouts,
    }


def run_ecosystem_test(n: int = 200):
    factions = [Faction.FRANCE, Faction.PRUSSIA, Faction.RUSSIA]
    
    print(f"\n{'='*70}")
    print(f"三阵营生态测试（每组对决 {n} 局）")
    print(f"{'='*70}\n")
    
    # 矩阵：行=先手，列=后手
    print(f"  {'先手 \\ 后手':<10}", end="")
    for f in factions:
        print(f"  {f.value:^14}", end="")
    print()
    print("-" * 70)
    
    matrix = {}
    
    for p1_f in factions:
        print(f"  {p1_f.value:<10}", end="")
        for p2_f in factions:
            if p1_f == p2_f:
                # 镜像对决
                stats = test_matchup(p1_f, p2_f, n)
                wr = stats["p1_winrate"]
                turns = stats["avg_turns"]
                # 镜像看的是先手优势
                marker = "(镜)"
                print(f"  {wr*100:>5.1f}%/{turns:>4.1f}T{marker}", end="")
            else:
                stats = test_matchup(p1_f, p2_f, n)
                wr = stats["p1_winrate"]
                turns = stats["avg_turns"]
                print(f"  {wr*100:>5.1f}%/{turns:>4.1f}T   ", end="")
            matrix[(p1_f, p2_f)] = stats
        print()
    
    print("\n  注：% 是先手胜率，T 是平均回合数，(镜) = 镜像对决")
    
    # 计算每个阵营的"综合实力"（无视先后手）
    print(f"\n  阵营综合实力（合并先后手胜率）：")
    for f in factions:
        wins_as_p1 = sum(matrix[(f, opp)]["p1_winrate"] for opp in factions if opp != f)
        wins_as_p2 = sum(1 - matrix[(opp, f)]["p1_winrate"] for opp in factions if opp != f)
        # 4 个数据点（2 个非镜像对决 × 先后手），平均
        overall = (wins_as_p1 + wins_as_p2) / 4
        print(f"    {f.value}: {overall*100:.1f}%")
    
    # 健康度评估
    print(f"\n  健康度评估：")
    issues = []
    
    # 检查每个阵营的综合胜率
    for f in factions:
        wins_as_p1 = sum(matrix[(f, opp)]["p1_winrate"] for opp in factions if opp != f)
        wins_as_p2 = sum(1 - matrix[(opp, f)]["p1_winrate"] for opp in factions if opp != f)
        overall = (wins_as_p1 + wins_as_p2) / 4
        if overall < 0.40:
            issues.append(f"⚠️  {f.value} 综合胜率 {overall*100:.1f}% 偏低")
        if overall > 0.60:
            issues.append(f"⚠️  {f.value} 综合胜率 {overall*100:.1f}% 偏高")
    
    # 检查超时
    total_timeouts = sum(matrix[k]["timeouts"] for k in matrix)
    if total_timeouts > n * 6 * 0.05:
        issues.append(f"⚠️  超时局过多：{total_timeouts}")
    
    # 检查回合数极端
    for k, stats in matrix.items():
        if stats["avg_turns"] > 20:
            issues.append(f"⚠️  {k[0].value} vs {k[1].value} 平均 {stats['avg_turns']:.1f} 回合，过长")
    
    if not issues:
        print("    ✅ 三阵营生态健康")
    else:
        for issue in issues:
            print(f"    {issue}")
    
    return matrix


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    run_ecosystem_test(n)
