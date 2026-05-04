"""
批量模拟器：跑 N 局两个 AI 互打，输出关键指标

我们要回答：
1. 平均回合数（目标 10-15）
2. 胜率分布（目标双方都接近 50%，否则平衡有问题）
3. 是否经常超时（>30%超时说明对局节奏太慢）
4. 平均部署单位数（衡量场面活跃度）
5. HQ 残血分布（衡量优势局是否容易翻盘）
"""

import statistics
import sys
import io
from collections import Counter
from cards import Faction
from game import STARTING_HQ_HP, play_one_game


def run_batch(n_games: int = 100, p1_faction=Faction.FRANCE, p2_faction=Faction.PRUSSIA):
    """跑 N 局，输出统计"""
    results = []
    for i in range(n_games):
        # 抑制游戏内部 print（如有）
        result = play_one_game(p1_faction=p1_faction, p2_faction=p2_faction, 
                               verbose=False, seed=i)
        results.append(result)
    
    # 统计
    p1_wins = sum(1 for r in results if r.winner == 0)
    p2_wins = sum(1 for r in results if r.winner == 1)
    draws = sum(1 for r in results if r.winner == -1)
    
    timeouts = sum(1 for r in results if "超时" in r.end_reason)
    
    turns = [r.turns for r in results]
    avg_turns = statistics.mean(turns)
    median_turns = statistics.median(turns)
    
    p1_units = [r.p1_units_played for r in results]
    p2_units = [r.p2_units_played for r in results]
    
    p1_hq_remaining = [r.p1_hq_remaining for r in results if r.winner == 0]
    p2_hq_remaining = [r.p2_hq_remaining for r in results if r.winner == 1]
    
    print(f"\n{'='*60}")
    print(f"对局统计：{n_games} 局 ({p1_faction.value} 先手 vs {p2_faction.value} 后手)")
    print(f"{'='*60}")
    
    print(f"\n📊 胜负分布：")
    print(f"  P1（{p1_faction.value}）胜：{p1_wins}/{n_games} = {p1_wins/n_games*100:.1f}%")
    print(f"  P2（{p2_faction.value}）胜：{p2_wins}/{n_games} = {p2_wins/n_games*100:.1f}%")
    print(f"  平局：{draws}/{n_games} = {draws/n_games*100:.1f}%")
    print(f"  超时局：{timeouts}/{n_games} = {timeouts/n_games*100:.1f}%")
    
    print(f"\n⏱️  对局长度：")
    print(f"  平均回合：{avg_turns:.1f}")
    print(f"  中位回合：{median_turns}")
    print(f"  最短：{min(turns)}, 最长：{max(turns)}")
    
    # 回合数分布直方图
    print(f"\n  回合数分布：")
    turn_buckets = Counter()
    for t in turns:
        if t <= 5: turn_buckets["1-5"] += 1
        elif t <= 10: turn_buckets["6-10"] += 1
        elif t <= 15: turn_buckets["11-15"] += 1
        elif t <= 20: turn_buckets["16-20"] += 1
        elif t <= 25: turn_buckets["21-25"] += 1
        else: turn_buckets["26-30"] += 1
    for bucket in ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30"]:
        count = turn_buckets.get(bucket, 0)
        bar = "█" * int(count / n_games * 50)
        print(f"    {bucket:>6}: {count:>3} {bar}")
    
    print(f"\n🎯 场面活跃度：")
    print(f"  P1 平均部署单位数：{statistics.mean(p1_units):.1f}")
    print(f"  P2 平均部署单位数：{statistics.mean(p2_units):.1f}")
    
    if p1_hq_remaining:
        print(f"\n💥 优势方残血（衡量是否容易翻盘）：")
        print(f"  P1 胜局 HQ 平均残血：{statistics.mean(p1_hq_remaining):.1f} / {STARTING_HQ_HP}")
        print(f"  P1 胜局 HQ 最低残血：{min(p1_hq_remaining)}")
    if p2_hq_remaining:
        print(f"  P2 胜局 HQ 平均残血：{statistics.mean(p2_hq_remaining):.1f} / {STARTING_HQ_HP}")
        print(f"  P2 胜局 HQ 最低残血：{min(p2_hq_remaining)}")
    
    # 健康度评估
    print(f"\n🏥 健康度评估：")
    issues = []
    if abs(p1_wins - p2_wins) / n_games > 0.20:
        issues.append(f"⚠️  胜率差距 >20%（先后手或阵营失衡）")
    if avg_turns < 6:
        issues.append(f"⚠️  对局过短（<6 回合，可能 rush 太强）")
    if avg_turns > 20:
        issues.append(f"⚠️  对局过长（>20 回合，节奏拖沓）")
    if timeouts / n_games > 0.10:
        issues.append(f"⚠️  超时率 >10%（{timeouts/n_games*100:.0f}%），无法正常分胜负")
    if not issues:
        print("  ✅ 节奏健康，胜率均衡，无明显失衡")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    return results


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_batch(n)
