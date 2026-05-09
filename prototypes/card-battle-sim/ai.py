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
from cards import Card, CardType, Line, UnitType
from game_state import Player, Battlefield, BattleUnit
from combat import find_attack_targets, can_attack_hq, calculate_damage, effective_attack


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
        if card.card_type == CardType.EVENT:
            if not _event_has_legal_target(card, battlefield, player_idx):
                continue
        else:
            target_line = Line.REAR  # UNIT 卡只能从后方部署
            if not battlefield.can_deploy(player_idx, target_line):
                continue
        cards_to_play.append(card)
        budget -= card.cost

    return cards_to_play


def _event_has_legal_target(card: Card, battlefield: Battlefield, player_idx: int) -> bool:
    """事件卡能否合法打出（是否有合法目标）"""
    enemy_idx = 1 - player_idx
    eff = card.event_effect

    if eff == "buff_target_INF+1+2":
        return any(u.card.unit_type == UnitType.INFANTRY
                   for u in battlefield.all_units(player_idx))

    if eff == "advance_friendly_one_no_attack":
        for from_line, to_line in [(Line.REAR, Line.MAIN), (Line.MAIN, Line.SKIRMISH)]:
            if any(not u.has_acted_this_turn
                   and not u.is_shaken
                   and battlefield.can_deploy(player_idx, to_line, u.slot)
                   for u in battlefield.get_line(player_idx, from_line)):
                return True
        return False

    if eff == "fortify_target_INF_GUARD+0+2_guard":
        return any(u.card.unit_type in (UnitType.INFANTRY, UnitType.GUARD)
                   for u in battlefield.all_units(player_idx))

    if eff == "draw1_buff_target_INF+1+1":
        return any(u.card.unit_type == UnitType.INFANTRY
                   for u in battlefield.all_units(player_idx))

    if eff == "buff_all_friendly_CAV_GUARD+1":
        return any(u.card.unit_type in (UnitType.CAVALRY, UnitType.GUARD)
                   for u in battlefield.all_units(player_idx))

    if eff == "retreat_friendly_heal2_hq1":
        return any(u.current_line in (Line.MAIN, Line.SKIRMISH)
                   and battlefield.can_deploy(player_idx, Line.REAR, u.slot)
                   for u in battlefield.all_units(player_idx))

    if eff == "self_hq1_damage_enemy_skirmish1":
        return len(battlefield.get_line(enemy_idx, Line.SKIRMISH)) > 0

    if eff == "weather_fog_artillery-1":
        return any(u.card.unit_type == UnitType.ARTILLERY and u.card.attack > 0
                   for u in battlefield.all_units(player_idx) + battlefield.all_units(enemy_idx))

    if eff == "weather_mud_cavalry-1":
        return any(u.card.unit_type == UnitType.CAVALRY and u.card.attack > 0
                   for u in battlefield.all_units(player_idx) + battlefield.all_units(enemy_idx))

    if eff == "weather_winter_all_damage1":
        return len(battlefield.all_units(player_idx) + battlefield.all_units(enemy_idx)) > 0

    return True


def choose_units_to_advance(
    player: Player,
    battlefield: Battlefield,
    player_idx: int,
    from_line: Line = Line.MAIN,
    to_line: Line = Line.SKIRMISH,
) -> List[BattleUnit]:
    """选择要前压的单位

    前压成本：1 军令/单位
    优先前压：步兵和散兵（推进控线）
    不前压：炮兵（远程）、高费精锐（保护）
    """
    advancers = []
    source_line = battlefield.get_line(player_idx, from_line)
    target_capacity = Battlefield.LINE_CAPACITY - len(battlefield.occupied_slots(player_idx, to_line))

    if target_capacity <= 0:
        return []

    # 后方→主力：推步兵 / 骑兵 / 散兵 / 近卫（炮兵留后方远程）
    # 主力→散兵：步兵、骑兵、散兵都该上前线施压 HQ
    if from_line == Line.REAR:
        preferred_types = (UnitType.INFANTRY, UnitType.CAVALRY, UnitType.SKIRMISHER, UnitType.GUARD)
    else:
        preferred_types = (UnitType.INFANTRY, UnitType.CAVALRY, UnitType.SKIRMISHER)

    candidates = [u for u in source_line
                  if not u.deployed_this_turn
                  and not u.is_shaken
                  and (u.card.unit_type in preferred_types
                       or "阿尔科莱精神" in u.card.keywords)
                  and battlefield.can_deploy(player_idx, to_line, u.slot)]

    candidates.sort(key=lambda u: u.card.cost)

    for unit in candidates:
        if player.current_orders < 1:
            break
        if len(advancers) >= target_capacity:
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
        # 动摇单位是可趁势压垮的目标，但只作为小幅平局倾向，避免过度集火。
        if target.is_shaken:
            score += 3
        scored.append((score, target))
    
    # 取最高分
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def ai_attack_phase(
    player: Player,
    opponent: Player,
    battlefield: Battlefield,
    player_idx: int,
    log: list = None,
    sub_steps: list = None,
    snapshot_fn=None,
    enable_unit_synergies: bool = False,
    under_pressure: bool = False,
) -> int:
    def _snapshot():
        if snapshot_fn is None:
            return None
        return snapshot_fn(player, opponent, battlefield) if player_idx == 0 else snapshot_fn(opponent, player, battlefield)
    """执行攻击阶段，返回对 HQ 造成的总伤害"""
    from combat import execute_attack
    from game import MAX_ORDERS

    hq_damage = 0
    # 突破奖励：记录本回合清空的战线（每方每回合最多触发一次）
    breakthrough_lines = set()  # 存储 (line_enum,) 元组
    breakthrough_used = False

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
                dmg = effective_attack(attacker, battlefield, player_idx)
                # 突破奖励：从突破战线发起的首次 HQ 直击 +1
                breakthrough_bonus = 0
                if (not breakthrough_used and attacker.current_line in breakthrough_lines):
                    breakthrough_bonus = 1
                    breakthrough_used = True
                # 拿破仑指挥官：标记战线的首次 HQ 直击 +1
                commander_bonus = 0
                if getattr(player, "commander_active_line", None) == attacker.current_line:
                    commander_bonus = 1
                    player.commander_active_line = None
                dmg += breakthrough_bonus + commander_bonus
                opponent.hq_hp -= dmg
                hq_damage += dmg
                attacker.has_acted_this_turn = True
                if log is not None:
                    cost_note = "（-1军令）" if is_long_range_hq_strike else ""
                    bt_note = " +突破奖励" if breakthrough_bonus > 0 else ""
                    cmd_note = " +指挥官" if commander_bonus > 0 else ""
                    log.append(f"  💥 {attacker.card.name} 直击HQ，造成{dmg}点伤害{cost_note}{bt_note}{cmd_note}")
                if sub_steps is not None and snapshot_fn is not None:
                    sub_steps.append({
                        "action": "hq_attack",
                        "log": list(log) if log else [],
                        "attack_event": {
                            "attacker": {"owner": f"p{player_idx + 1}", "name": attacker.card.name, "line": attacker.current_line.value, "slot": attacker.slot},
                            "defender": {"owner": f"p{2 - player_idx}", "name": "HQ", "line": "hq", "slot": -1},
                            "dmg_to_defender": dmg,
                            "dmg_to_attacker": 0,
                            "defender_killed": opponent.hq_hp <= 0,
                            "attacker_killed": False,
                            "breakthrough": breakthrough_bonus > 0,
                        },
                        "state": _snapshot(),
                    })
                continue

        # 找目标
        legal_targets = find_attack_targets(battlefield, attacker, player_idx)
        if not legal_targets:
            continue

        target = choose_attack_target(attacker, legal_targets, battlefield, player_idx)
        if target is None:
            continue

        # 炮兵准备目标奖励：下一次炮兵攻击 +1
        objective_bonus = 0
        if (attacker.card.unit_type == UnitType.ARTILLERY
                and getattr(player, "objective_reward_pending", None) == "artillery_attack_plus_1"):
            objective_bonus = 1
            player.objective_reward_pending = None

        result = execute_attack(
            attacker, target, log,
            battlefield=battlefield,
            attacker_player_idx=player_idx,
            attack_bonus=objective_bonus,
            enable_unit_synergies=enable_unit_synergies,
            under_pressure=under_pressure,
        )
        if result["smash_overflow"]:
            opponent.hq_hp -= result["smash_overflow"]
            hq_damage += result["smash_overflow"]

        # 焦土补给：死亡触发拥有者下回合 +1 max_orders
        if result["defender_killed"] and "焦土补给" in target.card.keywords:
            opponent.max_orders = min(opponent.max_orders + 1, MAX_ORDERS)
            if log is not None:
                log.append(f"    🔥 焦土补给：{opponent.name} 下回合 max_orders +1 (现 {opponent.max_orders})")
        if result["attacker_killed"] and "焦土补给" in attacker.card.keywords:
            player.max_orders = min(player.max_orders + 1, MAX_ORDERS)
            if log is not None:
                log.append(f"    🔥 焦土补给：{player.name} 下回合 max_orders +1 (现 {player.max_orders})")

        # 熔岩战术：仅限 MAIN 线攻击后撤回 REAR
        # （SKIRMISH 攻击不触发：哥萨克前压到散兵线后被困在前线）
        if (not result["attacker_killed"]
                and "熔岩战术" in attacker.card.keywords
                and attacker.current_line == Line.MAIN):
            rear_slot = battlefield.choose_deploy_slot(player_idx, Line.REAR)
            if rear_slot is not None:
                battlefield.get_line(player_idx, attacker.current_line).remove(attacker)
                attacker.current_line = Line.REAR
                attacker.slot = rear_slot
                battlefield.get_line(player_idx, Line.REAR).append(attacker)
                battlefield.sort_line(player_idx, Line.REAR)
                if log is not None:
                    log.append(f"    🌋 熔岩战术：{attacker.card.name} 撤回后方")

        # 先快照再清理，确保被击杀的单位仍在快照中（箭头需要指向它）
        if sub_steps is not None and snapshot_fn is not None:
            sub_steps.append({
                "action": "attack",
                "log": list(log) if log else [],
                "attack_event": {
                    "attacker": {"owner": f"p{player_idx + 1}", **result["attacker_pos"]},
                    "attacker_name": result["attacker"],
                    "defender": {"owner": f"p{2 - player_idx}", **result["defender_pos"]},
                    "defender_name": result["defender"],
                    "dmg_to_defender": result["dmg_to_defender"],
                    "dmg_to_attacker": result["dmg_to_attacker"],
                    "defender_killed": result["defender_killed"],
                    "attacker_killed": result["attacker_killed"],
                    "defender_hp_after": result["defender_hp_after"],
                    "attacker_hp_after": result["attacker_hp_after"],
                    "damage_modifiers": result.get("damage_modifiers", []),
                },
                "state": _snapshot(),
            })

        battlefield.cleanup_dead()

        # 突破检测：击杀后如果敌方该线清空，且我方有单位在该线，标记突破
        if result["defender_killed"] and not breakthrough_used:
            enemy_idx = 1 - player_idx
            def_line_str = result["defender_pos"]["line"]
            # 将字符串映射到 Line 枚举
            line_map = {"后方线": Line.REAR, "主力战列线": Line.MAIN, "散兵线": Line.SKIRMISH}
            def_line = line_map.get(def_line_str)
            if def_line is not None:
                enemy_on_line = battlefield.get_line(enemy_idx, def_line)
                friendly_on_line = battlefield.get_line(player_idx, def_line)
                if len(enemy_on_line) == 0 and len(friendly_on_line) > 0:
                    breakthrough_lines.add(def_line)
                    if log is not None:
                        log.append(f"  🏴 突破！{def_line.value} 已清空，下次直击 HQ +1")

    battlefield.cleanup_dead()
    return hq_damage
