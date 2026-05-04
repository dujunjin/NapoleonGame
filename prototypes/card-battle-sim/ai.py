"""
拿破仑卡牌游戏规则模拟器 - AI 决策

简单启发式 AI（不是强 AI），目的是验证规则不卡死，不是优化胜率。

决策优先级：
1. 如果能打 HQ，打 HQ（优先斩杀）
2. 如果敌方散兵线有单位，主力线先解决散兵
3. 攻击能一击必杀的目标（高效率交换）
4. 部署阶段：优先填散兵线 → 填主力 → 填后方
"""

import random
from typing import List, Optional, Tuple
from cards import Card, Line, UnitType
from game_state import Player, Battlefield, BattleUnit
from combat import find_attack_targets, can_attack_hq, calculate_damage


def choose_cards_to_play(player: Player, battlefield: Battlefield, player_idx: int) -> List[Card]:
    """决定这回合要打哪些牌
    
    策略：尽量花光军令，但留出 1-2 点用于前压。
    优先级：散兵 > 中费步兵 > 骑兵 > 炮兵 > 高费精锐
    """
    cards_to_play = []
    remaining_orders = player.current_orders
    hand_copy = list(player.hand)
    
    # 排序：cost 升序（先打便宜的，铺场）
    # 但保留 ~2 点军令用于前压
    reserve_for_advance = 2 if remaining_orders >= 5 else 0
    budget = remaining_orders - reserve_for_advance
    
    hand_copy.sort(key=lambda c: c.cost)
    
    for card in hand_copy:
        if card.cost > budget:
            continue
        target_line = card.deploy_line
        if not battlefield.can_deploy(player_idx, target_line):
            continue
        cards_to_play.append(card)
        budget -= card.cost
    
    return cards_to_play


def choose_units_to_advance(
    player: Player, 
    battlefield: Battlefield, 
    player_idx: int
) -> List[BattleUnit]:
    """选择要从主力线前压到散兵线的单位
    
    前压成本：1 军令/单位
    优先前压：步兵和散兵（推进控线）
    不前压：炮兵（远程）、高费精锐（保护）
    """
    advancers = []
    main_line = battlefield.get_line(player_idx, Line.MAIN)
    skirmish_capacity = Battlefield.LINE_CAPACITY - len(battlefield.occupied_slots(player_idx, Line.SKIRMISH))
    
    if skirmish_capacity <= 0:
        return []
    
    # 优先前压步兵（不是高费的精锐）
    candidates = [u for u in main_line 
                  if not u.deployed_this_turn  # 部署当回合不能前压（除非有冲锋）
                  and u.card.unit_type in (UnitType.INFANTRY, UnitType.SKIRMISHER)
                  and u.card.cost <= 4
                  and battlefield.can_deploy(player_idx, Line.SKIRMISH, u.slot)]  # 不隐式换槽
    
    # 按 cost 升序（前压便宜的先去送）
    candidates.sort(key=lambda u: u.card.cost)
    
    for unit in candidates:
        if player.current_orders < 1:
            break
        if len(advancers) >= skirmish_capacity:
            break
        advancers.append(unit)
    
    return advancers


def choose_attack_target(
    attacker: BattleUnit,
    legal_targets: List[BattleUnit],
    battlefield: Battlefield,
    attacker_player_idx: int
) -> Optional[BattleUnit]:
    """选择攻击目标
    
    优先级：
    1. 能一击杀的（最高效率）
    2. 高威胁目标（高攻击力的）
    3. 低 HP 目标（送葬）
    """
    if not legal_targets:
        return None
    
    # 评分每个目标
    scored = []
    for target in legal_targets:
        dmg_def, dmg_atk = calculate_damage(attacker, target)
        score = 0
        # 能击杀加大量分数
        if dmg_def >= target.current_hp:
            score += 100
            # 但如果自己也死了，扣分
            if dmg_atk >= attacker.current_hp:
                score -= 30
        # 优先打高攻击力的
        score += target.card.attack * 5
        # 略微优先打低血的
        score += (target.card.health - target.current_hp) * 2
        scored.append((score, target))
    
    # 取最高分
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def ai_attack_phase(
    player: Player,
    opponent: Player,
    battlefield: Battlefield,
    player_idx: int,
    log: list = None
) -> int:
    """执行攻击阶段，返回对 HQ 造成的总伤害"""
    from combat import execute_attack
    
    hq_damage = 0
    # 收集所有能行动的单位
    attackers = [u for u in battlefield.all_units(player_idx) if u.can_act]
    
    for attacker in attackers:
        if attacker.is_dead:
            continue
        
        # 优先攻击 HQ
        if can_attack_hq(battlefield, attacker, player_idx):
            # 远程炮兵打 HQ 需要额外 1 点军令（瞄准/校射成本）
            is_long_range_hq_strike = (
                attacker.current_line == Line.REAR 
                and "远程" in attacker.card.keywords
            )
            
            if is_long_range_hq_strike and player.current_orders < 1:
                # 军令不够，这门炮打不了 HQ，看能否打场上目标
                pass  # 落到下面的常规攻击逻辑
            else:
                if is_long_range_hq_strike:
                    player.current_orders -= 1
                dmg = attacker.card.attack
                opponent.hq_hp -= dmg
                hq_damage += dmg
                attacker.has_acted_this_turn = True
                if log is not None:
                    cost_note = "（-1军令）" if is_long_range_hq_strike else ""
                    log.append(f"  💥 {attacker.card.name} 直击HQ，造成{dmg}点伤害{cost_note}")
                continue
        
        # 找目标
        legal_targets = find_attack_targets(battlefield, attacker, player_idx)
        if not legal_targets:
            continue
        
        target = choose_attack_target(attacker, legal_targets, battlefield, player_idx)
        if target is None:
            continue
        
        result = execute_attack(attacker, target, log)
        if result["smash_overflow"]:
            opponent.hq_hp -= result["smash_overflow"]
            hq_damage += result["smash_overflow"]
        battlefield.cleanup_dead()
    
    battlefield.cleanup_dead()
    return hq_damage
