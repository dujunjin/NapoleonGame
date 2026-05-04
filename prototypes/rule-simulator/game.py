"""
拿破仑卡牌游戏规则模拟器 - 主对局循环

回合流程：
1. 抽牌（每回合 1 张）
2. 恢复军令（max+1，封顶 10；current 重置为 max）
3. 部署阶段（打牌）
4. 攻击阶段
5. 检查胜负
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional
from cards import Card, Faction, build_france_deck, build_prussia_deck
from game_state import Player, Battlefield, BattleUnit
from ai import choose_cards_to_play, ai_attack_phase, choose_units_to_advance
from cards import Line, UnitType


# ========== 配置 ==========
STARTING_HQ_HP = 20         # HQ 起始血量
STARTING_HAND_SIZE = 4      # 起手抽牌
INITIAL_ORDERS = 2          # 起始军令
ORDERS_GROWTH_PER_TURN = 1  # 每回合军令+1
MAX_ORDERS = 10             # 军令上限
MAX_TURNS = 30              # 防止死循环


@dataclass
class GameResult:
    winner: int               # 0 / 1，平局为 -1
    turns: int
    p1_hq_remaining: int
    p2_hq_remaining: int
    p1_units_played: int
    p2_units_played: int
    end_reason: str


def deploy_card(player: Player, card: Card, battlefield: Battlefield, 
                player_idx: int, log: list = None) -> bool:
    """部署一张卡到战场
    
    根据卡牌的 deploy_line 部署到对应线（散兵线 / 主力 / 后方）
    """
    target_line = card.deploy_line
    if not battlefield.can_deploy(player_idx, target_line):
        return False
    
    unit = BattleUnit(
        card=card,
        current_hp=card.health,
        current_line=target_line,
        deployed_this_turn=True,
    )
    battlefield.get_line(player_idx, target_line).append(unit)
    player.hand.remove(card)
    player.current_orders -= card.cost
    
    if log is not None:
        log.append(f"  ▶ {player.name} 部署 {card.name} 到 {target_line.value}")
    return True


def play_turn(
    active: Player,
    opponent: Player,
    battlefield: Battlefield,
    active_idx: int,
    turn_num: int,
    log: list = None
) -> dict:
    """执行一个回合，返回该回合统计"""
    stats = {"units_played": 0, "hq_damage_dealt": 0}
    
    if log is not None:
        log.append(f"\n=== 回合 {turn_num}：{active.name} 行动 ===")
    
    # 1. 抽牌
    drawn = active.draw(1)
    
    # 2. 军令恢复
    active.max_orders = min(active.max_orders + ORDERS_GROWTH_PER_TURN, MAX_ORDERS)
    active.current_orders = active.max_orders
    
    # 重置场上单位的"本回合行动"标记
    for unit in battlefield.all_units(active_idx):
        unit.has_acted_this_turn = False
        unit.deployed_this_turn = False
    
    if log is not None:
        log.append(f"  抽到 {drawn[0].name if drawn else '(牌库空)'}")
        log.append(f"  军令: {active.current_orders}/{active.max_orders}")
        log.append(f"  手牌: {[c.name for c in active.hand]}")
    
    # 3. 部署阶段
    cards_to_play = choose_cards_to_play(active, battlefield, active_idx)
    for card in cards_to_play:
        # 重新检查（可能因为前面部署导致线满了）
        if active.current_orders >= card.cost and battlefield.can_deploy(active_idx, card.deploy_line):
            if deploy_card(active, card, battlefield, active_idx, log):
                stats["units_played"] += 1
                # 标记新部署的单位
                last_unit = battlefield.get_line(active_idx, card.deploy_line)[-1]
                last_unit.deployed_this_turn = True
    
    # 3.5 前压阶段：把主力线的步兵推到散兵线（消耗1军令）
    from ai import choose_units_to_advance
    advancers = choose_units_to_advance(active, battlefield, active_idx)
    for unit in advancers:
        if active.current_orders < 1:
            break
        if not battlefield.can_deploy(active_idx, Line.SKIRMISH):
            break
        # 从主力线移除
        battlefield.get_line(active_idx, Line.MAIN).remove(unit)
        # 加入散兵线
        unit.current_line = Line.SKIRMISH
        battlefield.get_line(active_idx, Line.SKIRMISH).append(unit)
        active.current_orders -= 1
        stats["advances"] = stats.get("advances", 0) + 1
        if log is not None:
            log.append(f"  ⇒ {unit.card.name} 前压到散兵线（-1军令）")
    
    # 4. 攻击阶段
    hq_damage = ai_attack_phase(active, opponent, battlefield, active_idx, log)
    stats["hq_damage_dealt"] = hq_damage
    
    if log is not None:
        log.append(f"  状态：P1 HQ={battlefield.p1_rear and 'X' or ''}{active.hq_hp if active_idx == 0 else opponent.hq_hp}, "
                   f"P2 HQ={active.hq_hp if active_idx == 1 else opponent.hq_hp}")
    
    return stats


def play_one_game(p1_faction: Faction = Faction.FRANCE, 
                  p2_faction: Faction = Faction.PRUSSIA,
                  verbose: bool = False,
                  seed: Optional[int] = None) -> GameResult:
    """执行完整一局对战"""
    if seed is not None:
        random.seed(seed)
    
    log = [] if verbose else None
    
    # 初始化玩家
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
    
    # 起始军令
    p1.max_orders = INITIAL_ORDERS
    p1.current_orders = INITIAL_ORDERS
    p2.max_orders = INITIAL_ORDERS
    p2.current_orders = INITIAL_ORDERS
    # 后手补偿：多抽 2 张
    p2.draw(2)
    
    battlefield = Battlefield()
    
    p1_units_played = 0
    p2_units_played = 0
    
    # 主循环：先后手交替
    for turn in range(1, MAX_TURNS + 1):
        # P1 回合
        stats = play_turn(p1, p2, battlefield, 0, turn, log)
        p1_units_played += stats["units_played"]
        
        if p2.hq_hp <= 0:
            return GameResult(winner=0, turns=turn, 
                              p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                              p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                              end_reason="P2 HQ 摧毁")
        
        # P2 回合
        stats = play_turn(p2, p1, battlefield, 1, turn, log)
        p2_units_played += stats["units_played"]
        
        if p1.hq_hp <= 0:
            if verbose and log:
                print("\n".join(log))
            return GameResult(winner=1, turns=turn,
                              p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                              p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                              end_reason="P1 HQ 摧毁")
    
    # 平局：30 回合还没分胜负
    if verbose and log:
        print("\n".join(log))
    # 按 HQ 残血判定
    if p1.hq_hp > p2.hq_hp:
        winner = 0
    elif p2.hq_hp > p1.hq_hp:
        winner = 1
    else:
        winner = -1
    return GameResult(winner=winner, turns=MAX_TURNS,
                      p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                      p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                      end_reason=f"超时 ({MAX_TURNS} 回合)")


if __name__ == "__main__":
    # 跑一局详细日志
    print("=" * 60)
    print("详细对战日志（法兰西 vs 普鲁士）")
    print("=" * 60)
    result = play_one_game(verbose=True, seed=42)
    print(f"\n=== 对局结果 ===")
    print(f"胜者: {'P1 法兰西' if result.winner == 0 else 'P2 普鲁士' if result.winner == 1 else '平局'}")
    print(f"回合数: {result.turns}")
    print(f"结束原因: {result.end_reason}")
    print(f"P1 HQ 剩余: {result.p1_hq_remaining}, P2 HQ 剩余: {result.p2_hq_remaining}")
    print(f"P1 部署单位: {result.p1_units_played}, P2 部署单位: {result.p2_units_played}")
