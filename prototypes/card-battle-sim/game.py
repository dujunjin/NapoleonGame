"""
拿破仑卡牌游戏规则模拟器 - 主对局循环

回合流程：
1. 抽牌（每轮抽 2 张，手牌上限 7）
2. 恢复军令（第 1 回合 1 点；每回合 +1；封顶 16）
3. 部署阶段（打牌）
4. 攻击阶段
5. 检查胜负
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional
from cards import Card, CardType, Faction, build_france_deck, build_prussia_deck, build_russia_deck, DECK_BUILDERS
from game_state import Player, Battlefield, BattleUnit, PlayEntry
from ai import choose_cards_to_play, ai_attack_phase, choose_units_to_advance
from cards import Line, UnitType
from commanders import get_default_commander
from objectives import assign_objectives


# ========== 配置 ==========
STARTING_HQ_HP = 14         # HQ 起始血量；配合同轮结算，给后手保留反击窗口
STARTING_HAND_SIZE = 4      # 起手抽牌
SECOND_PLAYER_BONUS_DRAW = 1 # 后手额外起手牌
TURN_DRAW_COUNT = 2         # 每轮发牌
MAX_HAND_SIZE = 7           # 手牌上限
INITIAL_ORDERS = 1          # 起始军令
ORDERS_GROWTH_PER_TURN = 1  # 每回合军令+1
MAX_ORDERS = 16             # 军令上限
MAX_TURNS = 30              # 倒计时上限（40→30，收紧节奏）
OPERATIONAL_PRESSURE_START_TURN = 18  # 作战压力起始回合


@dataclass
class GameResult:
    winner: int               # 0 / 1，平局为 -1
    turns: int
    p1_hq_remaining: int
    p2_hq_remaining: int
    p1_units_played: int
    p2_units_played: int
    end_reason: str
    first_hq_damage_turn: int = 0  # 首次 HQ 受伤的回合（0 = 未受伤）
    p1_commander: str = ""
    p2_commander: str = ""
    p1_objective: str = ""
    p2_objective: str = ""
    p1_objective_completed: bool = False
    p2_objective_completed: bool = False


def draw_for_turn(player: Player) -> List[Card]:
    """回合开始抽 2 张；手牌达到上限时不再发牌。"""
    return player.draw(TURN_DRAW_COUNT)


def advance_max_orders(current_max_orders: int, turn_num: int) -> int:
    """计算本回合军令上限：第 1 回合为 1，之后每回合 +1，封顶 16。"""
    if turn_num <= 1:
        return min(max(current_max_orders, INITIAL_ORDERS), MAX_ORDERS)
    return min(current_max_orders + ORDERS_GROWTH_PER_TURN, MAX_ORDERS)


def deploy_card(player: Player, card: Card, battlefield: Battlefield,
                player_idx: int, log: list = None, slot: int = None) -> bool:
    """部署一张卡到战场（UNIT），或解析事件卡（EVENT）。

    部署效果（on-play）：
    - "自残N"：对自己 HQ 造成 N 点伤害
    - "光环+1攻" / "光环+1血"：所有其他友军获得永久增益
    """
    if card.card_type == CardType.EVENT:
        success = _play_event_card(player, card, battlefield, player_idx, log)
        if success:
            player.play_log.append(PlayEntry(
                card_name=card.name,
                card_type="event",
                faction=card.faction.value,
                cost=card.cost,
                keywords=list(card.keywords),
            ))
        return success

    target_line = Line.REAR  # 新规则：所有 UNIT 卡只能从后方线部署
    target_slot = slot if slot is not None else battlefield.choose_deploy_slot(player_idx, target_line)
    if target_slot is None or not battlefield.can_deploy(player_idx, target_line, target_slot):
        return False
    
    unit = BattleUnit(
        card=card,
        current_hp=card.health,
        current_line=target_line,
        slot=target_slot,
        deployed_this_turn=True,
    )
    battlefield.get_line(player_idx, target_line).append(unit)
    battlefield.sort_line(player_idx, target_line)
    player.hand.remove(card)
    player.discard_pile.append(card)
    player.current_orders -= card.cost

    # v0.3B: Append to PlayLog
    player.play_log.append(PlayEntry(
        card_name=card.name,
        card_type="unit",
        unit_type=card.unit_type.value,
        faction=card.faction.value,
        subfaction=card.subfaction.value if card.subfaction else None,
        cost=card.cost,
        keywords=list(card.keywords),
    ))

    if log is not None:
        log.append(f"  ▶ {player.name} 部署 {card.name} 到 {target_line.value} 槽位{target_slot + 1}")
    
    # v0.3B: Landwehr max HP bonus at deployment
    if card.subfaction and card.subfaction.value == "landwehr":
        from triggers import LANDWEHR_HP_CAP
        landwehr_count = sum(
            1 for u in battlefield.all_units(player_idx)
            if u.card.subfaction and u.card.subfaction.value == "landwehr"
        )
        hp_bonus = min(landwehr_count, LANDWEHR_HP_CAP)
        unit.card = _apply_aura(unit.card, health_bonus=hp_bonus)
        unit.current_hp += hp_bonus

    # === 部署效果 ===
    for kw in card.keywords:
        # 自残 HQ
        if kw.startswith("自残"):
            damage = int(kw[2:])
            player.hq_hp -= damage
            if log is not None:
                log.append(f"    ⚠ 自残：HQ -{damage} (剩{player.hq_hp})")
        
        # 光环 +N 攻
        if kw.startswith("光环+1攻"):
            for u in battlefield.all_units(player_idx):
                if u is not unit:  # 不影响自己
                    u.card = _apply_aura(u.card, attack_bonus=1)
            if log is not None:
                log.append(f"    ✨ 光环：所有其他友军 +1 攻")
        
        # 光环 +N 血
        if kw.startswith("光环+1血"):
            for u in battlefield.all_units(player_idx):
                if u is not unit:
                    old_card = u.card
                    u.card = _apply_aura(u.card, health_bonus=1)
                    u.current_hp += 1  # 当前 hp 也 +1（不只是上限）
            if log is not None:
                log.append(f"    ✨ 光环：所有其他友军 +1 血")

    # v0.3B: On Deploy trigger
    unit.on_deploy_fired = True

    return True


def _apply_aura(card: Card, attack_bonus: int = 0, health_bonus: int = 0) -> Card:
    """生成一个数值修改后的 Card 副本（光环效果）"""
    from dataclasses import replace
    return replace(card,
                   attack=card.attack + attack_bonus,
                   health=card.health + health_bonus)


def _spend_event_card(player: Player, card: Card):
    player.hand.remove(card)
    player.discard_pile.append(card)
    player.current_orders -= card.cost


def _heal(unit: BattleUnit, amount: int):
    unit.current_hp = min(unit.card.health, unit.current_hp + amount)


def _with_keyword(card: Card, keyword: str) -> Card:
    from dataclasses import replace
    if keyword in card.keywords:
        return card
    return replace(card, keywords=card.keywords + [keyword])


def _move_unit(battlefield: Battlefield, player_idx: int, unit: BattleUnit,
               from_line: Line, to_line: Line):
    battlefield.get_line(player_idx, from_line).remove(unit)
    unit.current_line = to_line
    unit.has_acted_this_turn = True
    battlefield.get_line(player_idx, to_line).append(unit)
    battlefield.sort_line(player_idx, to_line)


def _play_event_card(player: Player, card: Card, battlefield: Battlefield,
                     player_idx: int, log: list = None) -> bool:
    """解析事件卡，不上场。失败（无合法目标 / 军令不足）返回 False。"""
    if player.current_orders < card.cost:
        return False

    enemy_idx = 1 - player_idx

    if card.event_effect == "buff_target_INF+1+2":
        targets = [u for u in battlefield.all_units(player_idx)
                   if u.card.unit_type == UnitType.INFANTRY]
        if not targets:
            return False
        target = min(targets, key=lambda u: u.current_hp)
        target.card = _apply_aura(target.card, attack_bonus=1, health_bonus=2)
        _heal(target, 2)
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ 强化 "
                       f"{target.card.name} (+1/+2)（现 {target.card.attack}/{target.card.health}, hp {target.current_hp}）")
        return True

    if card.event_effect == "advance_friendly_one_no_attack":
        # REAR→MAIN 优先，然后 MAIN→SKIRMISH
        for from_line, to_line in [(Line.REAR, Line.MAIN), (Line.MAIN, Line.SKIRMISH)]:
            candidates = [u for u in battlefield.get_line(player_idx, from_line)
                          if not u.has_acted_this_turn
                          and battlefield.can_deploy(player_idx, to_line, u.slot)]
            if candidates:
                target = candidates[0]
                _move_unit(battlefield, player_idx, target, from_line, to_line)
                _spend_event_card(player, card)
                if log is not None:
                    log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ "
                               f"{target.card.name} {from_line.value}→{to_line.value}")
                return True
        return False

    if card.event_effect == "fortify_target_INF_GUARD+0+2_guard":
        targets = [u for u in battlefield.all_units(player_idx)
                   if u.card.unit_type in (UnitType.INFANTRY, UnitType.GUARD)]
        if not targets:
            return False
        target = min(targets, key=lambda u: u.current_hp)
        target.card = _apply_aura(target.card, attack_bonus=0, health_bonus=2)
        target.card = _with_keyword(target.card, "守卫")
        _heal(target, 2)
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ "
                       f"{target.card.name} (+0/+2, 获得守卫)（hp {target.current_hp}）")
        return True

    if card.event_effect == "draw1_buff_target_INF+1+1":
        targets = [u for u in battlefield.all_units(player_idx)
                   if u.card.unit_type == UnitType.INFANTRY]
        if not targets:
            return False
        player.draw(1)
        target = min(targets, key=lambda u: u.current_hp)
        target.card = _apply_aura(target.card, attack_bonus=1, health_bonus=1)
        _heal(target, 1)
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ 抽1张，"
                       f"强化 {target.card.name} (+1/+1)（hp {target.current_hp}）")
        return True

    if card.event_effect == "buff_all_friendly_CAV_GUARD+1":
        targets = [u for u in battlefield.all_units(player_idx)
                   if u.card.unit_type in (UnitType.CAVALRY, UnitType.GUARD)]
        if not targets:
            return False
        for u in targets:
            u.card = _apply_aura(u.card, attack_bonus=1)
        _spend_event_card(player, card)
        if log is not None:
            names = "、".join(u.card.name for u in targets)
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ {names} +1 攻")
        return True

    if card.event_effect == "retreat_friendly_heal2_hq1":
        targets = [u for u in battlefield.all_units(player_idx)
                   if u.current_line in (Line.MAIN, Line.SKIRMISH)
                   and battlefield.can_deploy(player_idx, Line.REAR, u.slot)]
        if not targets:
            return False
        target = min(targets, key=lambda u: u.current_hp)
        _move_unit(battlefield, player_idx, target, target.current_line, Line.REAR)
        # _move_unit 已经改变了 current_line，这里用旧线做 remove 已不行
        # 修正：_move_unit 内部已经处理了，所以 target 已在 REAR
        _heal(target, 2)
        player.hq_hp -= 1
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ "
                       f"{target.card.name} 撤回后方，回复2血（hp {target.current_hp}），HQ -1")
        return True

    if card.event_effect == "self_hq1_damage_enemy_skirmish1":
        enemies = battlefield.get_line(enemy_idx, Line.SKIRMISH)
        if not enemies:
            return False
        player.hq_hp -= 1
        for u in enemies:
            u.current_hp -= 1
        battlefield.cleanup_dead()
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ HQ -1，敌方散兵线全体 -1 血")
        return True

    if card.event_effect == "weather_fog_artillery-1":
        targets = [u for u in battlefield.all_units(player_idx) + battlefield.all_units(enemy_idx)
                   if u.card.unit_type == UnitType.ARTILLERY and u.card.attack > 0]
        if not targets:
            return False
        for u in targets:
            u.card = _apply_aura(u.card, attack_bonus=-1)
            if u.card.attack < 0:
                u.card = _apply_aura(u.card, attack_bonus=-u.card.attack)
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ 全场炮兵 -1 攻")
        return True

    if card.event_effect == "weather_mud_cavalry-1":
        targets = [u for u in battlefield.all_units(player_idx) + battlefield.all_units(enemy_idx)
                   if u.card.unit_type == UnitType.CAVALRY and u.card.attack > 0]
        if not targets:
            return False
        for u in targets:
            u.card = _apply_aura(u.card, attack_bonus=-1)
            if u.card.attack < 0:
                u.card = _apply_aura(u.card, attack_bonus=-u.card.attack)
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ 全场骑兵 -1 攻")
        return True

    if card.event_effect == "weather_winter_all_damage1":
        all_units = battlefield.all_units(player_idx) + battlefield.all_units(enemy_idx)
        if not all_units:
            return False
        for u in all_units:
            u.current_hp -= 1
        battlefield.cleanup_dead()
        _spend_event_card(player, card)
        if log is not None:
            log.append(f"  📜 {player.name} 打出事件卡【{card.name}】→ 全场所有单位 -1 血")
        return True

    return False


def play_turn(
    active: Player,
    opponent: Player,
    battlefield: Battlefield,
    active_idx: int,
    turn_num: int,
    log: list = None,
    sub_steps: list = None,
    snapshot_fn=None,
) -> dict:
    """执行一个回合，返回该回合统计"""
    stats = {"units_played": 0, "hq_damage_dealt": 0}
    
    if log is not None:
        log.append(f"\n=== 回合 {turn_num}：{active.name} 行动 ===")
    
    # 1. 抽牌
    drawn = draw_for_turn(active)
    
    # 2. 军令恢复
    active.max_orders = advance_max_orders(active.max_orders, turn_num)
    active.current_orders = active.max_orders
    
    # 重置场上单位的"本回合行动"标记
    for unit in battlefield.all_units(active_idx):
        unit.has_acted_this_turn = False
        unit.deployed_this_turn = False
        if unit.damage_reduction_turns > 0:
            unit.damage_reduction_turns -= 1

    # v0.3B: Reset PlayLog at turn start
    active.play_log = []
    
    if log is not None:
        if drawn:
            drawn_names = "、".join(card.name for card in drawn)
        elif len(active.hand) >= MAX_HAND_SIZE:
            drawn_names = "(手牌已满)"
        else:
            drawn_names = "(牌库空)"
        log.append(f"  抽到 {drawn_names}")
        log.append(f"  军令: {active.current_orders}/{active.max_orders}")
        log.append(f"  手牌: {[c.name for c in active.hand]}")
    
    # 3. 部署阶段
    cards_to_play = choose_cards_to_play(active, battlefield, active_idx)
    for card in cards_to_play:
        if active.current_orders < card.cost:
            continue
        # UNIT 卡需要 REAR 有空位；事件卡跳过该检查
        if card.card_type == CardType.UNIT and not battlefield.can_deploy(active_idx, Line.REAR):
            continue
        if deploy_card(active, card, battlefield, active_idx, log):
            if card.card_type == CardType.UNIT:
                stats["units_played"] += 1
            else:
                stats["events_played"] = stats.get("events_played", 0) + 1
            if sub_steps is not None and snapshot_fn is not None:
                sub_steps.append({
                    "action": "deploy",
                    "log": list(log) if log else [],
                    "state": snapshot_fn(active, opponent, battlefield) if active_idx == 0 else snapshot_fn(opponent, active, battlefield),
                })
    
    # 3.5 前压阶段：后方→主力→散兵（每步消耗1军令）
    from ai import choose_units_to_advance

    # 先推后方→主力
    rear_advancers = choose_units_to_advance(active, battlefield, active_idx, from_line=Line.REAR, to_line=Line.MAIN)
    for unit in rear_advancers:
        if active.current_orders < 1:
            break
        if not battlefield.can_deploy(active_idx, Line.MAIN, unit.slot):
            continue
        battlefield.get_line(active_idx, Line.REAR).remove(unit)
        unit.current_line = Line.MAIN
        unit.has_acted_this_turn = True
        battlefield.get_line(active_idx, Line.MAIN).append(unit)
        battlefield.sort_line(active_idx, Line.MAIN)
        active.current_orders -= 1
        stats["advances"] = stats.get("advances", 0) + 1
        if log is not None:
            log.append(f"  ⇒ {unit.card.name} 后方→主力 槽位{unit.slot + 1}（-1军令）")
        if sub_steps is not None and snapshot_fn is not None:
            sub_steps.append({
                "action": "advance",
                "log": list(log) if log else [],
                "state": snapshot_fn(active, opponent, battlefield) if active_idx == 0 else snapshot_fn(opponent, active, battlefield),
            })

    # 再推主力→散兵
    main_advancers = choose_units_to_advance(active, battlefield, active_idx, from_line=Line.MAIN, to_line=Line.SKIRMISH)
    for unit in main_advancers:
        if active.current_orders < 1:
            break
        if not battlefield.can_deploy(active_idx, Line.SKIRMISH, unit.slot):
            continue
        battlefield.get_line(active_idx, Line.MAIN).remove(unit)
        unit.current_line = Line.SKIRMISH
        unit.has_acted_this_turn = True
        battlefield.get_line(active_idx, Line.SKIRMISH).append(unit)
        battlefield.sort_line(active_idx, Line.SKIRMISH)
        active.current_orders -= 1
        # 阿尔科莱精神：到达散兵线时攻击力 +2，伤害减免2回合
        if "阿尔科莱精神" in unit.card.keywords:
            from dataclasses import replace
            unit.card = replace(unit.card, attack=unit.card.attack + 2)
            unit.damage_reduction_turns = 2
            if log is not None:
                log.append(f"    ✨ 阿尔科莱精神：{unit.card.name} 攻击力 +2（现{unit.card.attack}），伤害减免2回合")
        stats["advances"] = stats.get("advances", 0) + 1
        if log is not None:
            log.append(f"  ⇒ {unit.card.name} 主力→散兵 槽位{unit.slot + 1}（-1军令）")
        if sub_steps is not None and snapshot_fn is not None:
            sub_steps.append({
                "action": "advance",
                "log": list(log) if log else [],
                "state": snapshot_fn(active, opponent, battlefield) if active_idx == 0 else snapshot_fn(opponent, active, battlefield),
            })

    # 4. 攻击阶段（指挥官能力在攻击前使用）
    use_commander_ability(active, opponent, battlefield, active_idx, turn_num, log)
    hq_damage = ai_attack_phase(active, opponent, battlefield, active_idx, log,
                                sub_steps=sub_steps, snapshot_fn=snapshot_fn)
    stats["hq_damage_dealt"] = hq_damage
    
    if log is not None:
        log.append(f"  状态：P1 HQ={battlefield.p1_rear and 'X' or ''}{active.hq_hp if active_idx == 0 else opponent.hq_hp}, "
                   f"P2 HQ={active.hq_hp if active_idx == 1 else opponent.hq_hp}")

    return stats


def apply_operational_pressure(p1: Player, p2: Player,
                               p1_dealt_hq_damage: bool,
                               p2_dealt_hq_damage: bool,
                               turn: int,
                               log: Optional[List[str]] = None) -> None:
    """Apply round-end pressure to players who failed to damage enemy HQ."""
    if turn < OPERATIONAL_PRESSURE_START_TURN:
        return

    if p1_dealt_hq_damage and not p2_dealt_hq_damage:
        p2.hq_hp -= 1
        if log is not None:
            log.append(f"  ⚡ 作战压力：{p2.name} 未造成 HQ 伤害，HQ -1")
    elif p2_dealt_hq_damage and not p1_dealt_hq_damage:
        p1.hq_hp -= 1
        if log is not None:
            log.append(f"  ⚡ 作战压力：{p1.name} 未造成 HQ 伤害，HQ -1")
    elif not p1_dealt_hq_damage and not p2_dealt_hq_damage:
        p1.hq_hp -= 1
        p2.hq_hp -= 1
        if log is not None:
            log.append("  ⚡ 作战压力：双方均未造成 HQ 伤害，各 HQ -1")


def initialize_command_layer(p1: Player, p2: Player, seed: int) -> None:
    p1_commander = get_default_commander(p1.faction)
    p2_commander = get_default_commander(p2.faction)
    p1.commander_id = p1_commander.id.value
    p1.commander_name = p1_commander.name
    p2.commander_id = p2_commander.id.value
    p2.commander_name = p2_commander.name

    p1_objective, p2_objective = assign_objectives(seed)
    p1.objective_id = p1_objective.id.value
    p1.objective_name = p1_objective.name
    p2.objective_id = p2_objective.id.value
    p2.objective_name = p2_objective.name


def use_commander_ability(player: Player, opponent: Player, battlefield: Battlefield,
                          player_idx: int, turn: int, log: Optional[List[str]] = None) -> bool:
    if player.commander_used or not player.commander_id:
        return False

    units = battlefield.all_units(player_idx)

    if player.commander_id == "napoleon":
        candidates = [u for u in units if not u.is_dead]
        if not candidates:
            return False
        chosen = max(candidates, key=lambda u: u.card.attack)
        player.commander_active_line = chosen.current_line
        player.commander_used = True
        player.commander_use_turn = turn
        if log is not None:
            log.append(f"  ★ {player.name} 使用指挥官【拿破仑】→ {chosen.current_line.value} 首次 HQ 直击 +1")
        return True

    if player.commander_id == "blucher":
        wounded = [u for u in units if not u.is_dead and u.current_hp < u.card.health]
        if not wounded:
            return False
        for unit in wounded:
            unit.card = _apply_aura(unit.card, attack_bonus=1)
        player.commander_used = True
        player.commander_use_turn = turn
        if log is not None:
            log.append(f"  ★ {player.name} 使用指挥官【布吕歇尔】→ {len(wounded)} 个受伤友军 +1 攻")
        return True

    if player.commander_id == "kutuzov":
        candidates = [u for u in units if not u.is_dead and u.current_line != Line.REAR]
        if not candidates:
            return False
        chosen = min(candidates, key=lambda u: (u.current_hp, -u.card.cost))
        battlefield.get_line(player_idx, chosen.current_line).remove(chosen)
        chosen.current_line = Line.REAR
        chosen.current_hp = min(chosen.card.health, chosen.current_hp + 1)
        chosen.has_acted_this_turn = True
        battlefield.get_line(player_idx, Line.REAR).append(chosen)
        battlefield.sort_line(player_idx, Line.REAR)
        player.hq_hp += 1
        player.commander_used = True
        player.commander_use_turn = turn
        if log is not None:
            log.append(f"  ★ {player.name} 使用指挥官【库图佐夫】→ {chosen.card.name} 撤回后方线，单位 +1 HP，HQ +1")
        return True

    return False


def check_action_objectives(player: Player, opponent: Player, battlefield: Battlefield,
                            player_idx: int, turn: int, dealt_hq_damage: bool,
                            log: Optional[List[str]] = None) -> None:
    if player.objective_completed or not player.objective_id:
        return
    from objectives import ObjectiveId, complete_objective
    if player.objective_id == ObjectiveId.SEIZE_SKIRMISH.value:
        if (len(battlefield.get_line(player_idx, Line.SKIRMISH)) >= 2
                and not battlefield.get_line(1 - player_idx, Line.SKIRMISH)):
            complete_objective(player, ObjectiveId.SEIZE_SKIRMISH, turn, log)
    elif player.objective_id == ObjectiveId.FIRST_BLOOD_HQ.value and dealt_hq_damage:
        complete_objective(player, ObjectiveId.FIRST_BLOOD_HQ, turn, log)
    elif player.objective_id == ObjectiveId.PREPARE_GUNS.value:
        rear_units = battlefield.get_line(player_idx, Line.REAR)
        if any(unit.card.unit_type == UnitType.ARTILLERY for unit in rear_units):
            complete_objective(player, ObjectiveId.PREPARE_GUNS, turn, log)


def check_round_objectives(p1: Player, p2: Player, battlefield: Battlefield,
                           turn: int,
                           p1_dealt_hq_damage: bool,
                           p2_dealt_hq_damage: bool,
                           p1_unit_died: bool,
                           p2_unit_died: bool,
                           log: Optional[List[str]] = None) -> None:
    from objectives import ObjectiveId, complete_objective
    if p1.objective_id == ObjectiveId.HOLD_MAIN.value and len(battlefield.p1_main) >= 3:
        complete_objective(p1, ObjectiveId.HOLD_MAIN, turn, log)
    if p2.objective_id == ObjectiveId.HOLD_MAIN.value and len(battlefield.p2_main) >= 3:
        complete_objective(p2, ObjectiveId.HOLD_MAIN, turn, log)

    if p1.objective_id == ObjectiveId.SACRIFICE_FOR_TIME.value and p1_unit_died and not p2_dealt_hq_damage:
        complete_objective(p1, ObjectiveId.SACRIFICE_FOR_TIME, turn, log)
    if p2.objective_id == ObjectiveId.SACRIFICE_FOR_TIME.value and p2_unit_died and not p1_dealt_hq_damage:
        complete_objective(p2, ObjectiveId.SACRIFICE_FOR_TIME, turn, log)


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
                deck=DECK_BUILDERS[p1_faction](),
                hq_hp=STARTING_HQ_HP)
    p2 = Player(name=f"P2-{p2_faction.value}", faction=p2_faction,
                deck=DECK_BUILDERS[p2_faction](),
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
    # 后手补偿：额外 1 张起手牌
    p2.draw(SECOND_PLAYER_BONUS_DRAW)
    
    battlefield = Battlefield()
    initialize_command_layer(p1, p2, seed if seed is not None else 0)

    p1_units_played = 0
    p2_units_played = 0
    first_hq_damage_turn = 0

    if log is not None:
        log.append(f"\n{'='*60}")
        log.append(f"  ⏳ 倒计时开始：最大 {MAX_TURNS} 回合")
        log.append(f"{'='*60}")

    # 主循环：先后手交替
    for turn in range(1, MAX_TURNS + 1):
        countdown = MAX_TURNS - turn

        if log is not None:
            log.append(f"\n--- 倒计时：剩余 {countdown} 回合 ---")

        p1_unit_died_this_round = False
        p2_unit_died_this_round = False

        # P1 回合
        p1_units_before = len(battlefield.all_units(0))
        p1_hq_before_p1, p2_hq_before_p1 = p1.hq_hp, p2.hq_hp
        stats = play_turn(p1, p2, battlefield, 0, turn, log)
        p1_units_played += stats["units_played"]
        p1_dealt_hq_damage = p2.hq_hp < p2_hq_before_p1
        if len(battlefield.all_units(0)) < p1_units_before:
            p1_unit_died_this_round = True
        if first_hq_damage_turn == 0 and (p1.hq_hp < p1_hq_before_p1 or p2.hq_hp < p2_hq_before_p1):
            first_hq_damage_turn = turn
        check_action_objectives(p1, p2, battlefield, 0, turn, p1_dealt_hq_damage, log)

        # P2 回合
        p2_units_before = len(battlefield.all_units(1))
        p1_hq_before_p2, p2_hq_before_p2 = p1.hq_hp, p2.hq_hp
        stats = play_turn(p2, p1, battlefield, 1, turn, log)
        p2_units_played += stats["units_played"]
        p2_dealt_hq_damage = p1.hq_hp < p1_hq_before_p2
        if len(battlefield.all_units(1)) < p2_units_before:
            p2_unit_died_this_round = True
        if first_hq_damage_turn == 0 and (p1.hq_hp < p1_hq_before_p2 or p2.hq_hp < p2_hq_before_p2):
            first_hq_damage_turn = turn
        check_action_objectives(p2, p1, battlefield, 1, turn, p2_dealt_hq_damage, log)

        # 回合结束目标检查
        check_round_objectives(
            p1, p2, battlefield, turn,
            p1_dealt_hq_damage=p1_dealt_hq_damage,
            p2_dealt_hq_damage=p2_dealt_hq_damage,
            p1_unit_died=p1_unit_died_this_round,
            p2_unit_died=p2_unit_died_this_round,
            log=log,
        )

        # 作战压力（Operational Pressure）：未对敌方 HQ 造成伤害的一方受到 1 点压力伤害
        apply_operational_pressure(
            p1, p2,
            p1_dealt_hq_damage=p1_dealt_hq_damage,
            p2_dealt_hq_damage=p2_dealt_hq_damage,
            turn=turn,
            log=log,
        )

        # 胜负在完整轮结束后统一结算，避免先手半回合斩杀直接跳过后手反击。
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
            if verbose and log:
                print("\n".join(log))
            return GameResult(winner=winner, turns=turn,
                              p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                              p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                              end_reason=end_reason, first_hq_damage_turn=first_hq_damage_turn,
                              p1_commander=p1.commander_name or "",
                              p2_commander=p2.commander_name or "",
                              p1_objective=p1.objective_name or "",
                              p2_objective=p2.objective_name or "",
                              p1_objective_completed=p1.objective_completed,
                              p2_objective_completed=p2.objective_completed)

        # 倒计时归零
        if countdown <= 0:
            if verbose and log:
                log.append(f"\n{'='*60}")
                log.append(f"  ⏰ 倒计时结束！比较 HQ 血量...")
                log.append(f"  P1 HQ: {p1.hq_hp}  vs  P2 HQ: {p2.hq_hp}")
                log.append(f"{'='*60}")
                print("\n".join(log))
            if p1.hq_hp > p2.hq_hp:
                winner = 0
            elif p2.hq_hp > p1.hq_hp:
                winner = 1
            else:
                winner = -1
            return GameResult(winner=winner, turns=MAX_TURNS,
                              p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                              p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                              end_reason=f"倒计时结束，HQ血量判定 (P1:{p1.hq_hp} vs P2:{p2.hq_hp})",
                              first_hq_damage_turn=first_hq_damage_turn,
                              p1_commander=p1.commander_name or "",
                              p2_commander=p2.commander_name or "",
                              p1_objective=p1.objective_name or "",
                              p2_objective=p2.objective_name or "",
                              p1_objective_completed=p1.objective_completed,
                              p2_objective_completed=p2.objective_completed)

    # 兜底（不应到达）
    if verbose and log:
        print("\n".join(log))
    if p1.hq_hp > p2.hq_hp:
        winner = 0
    elif p2.hq_hp > p1.hq_hp:
        winner = 1
    else:
        winner = -1
    return GameResult(winner=winner, turns=MAX_TURNS,
                      p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                      p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                      end_reason=f"超时 ({MAX_TURNS} 回合)",
                      first_hq_damage_turn=first_hq_damage_turn,
                      p1_commander=p1.commander_name or "",
                      p2_commander=p2.commander_name or "",
                      p1_objective=p1.objective_name or "",
                      p2_objective=p2.objective_name or "",
                      p1_objective_completed=p1.objective_completed,
                      p2_objective_completed=p2.objective_completed)


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
