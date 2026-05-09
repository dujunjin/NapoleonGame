"""
拿破仑卡牌游戏规则模拟器 - 战斗系统

核心规则：
1. 兵种克制：通过关键词 + 类型判断动态计算伤害
2. 目标选择：优先散兵线 → 主力线 → 后方
3. 守卫：场上有守卫单位时必须先打守卫
4. 侧翼迂回：散兵线的轻骑兵可以无视守卫直击后方炮兵
"""

from typing import List, Tuple, Optional
from cards import UnitType, Line
from game_state import BattleUnit, Battlefield
from triggers import IMPERIAL_GUARD_ATK_CAP


def maybe_mark_shaken(unit: BattleUnit, damage_taken: int, log: list = None) -> bool:
    """Apply 动摇/Shaken after damage if a surviving unit is at or below half base HP."""
    if damage_taken < 2 or unit.is_dead:
        return False
    if unit.current_hp * 2 > unit.base_max_hp:
        return False
    if not unit.mark_shaken():
        return False
    if log is not None:
        log.append(f"  ⚑ {unit.card.name} 动摇")
    return True


def is_under_morale_pressure(player, battlefield, player_idx: int) -> bool:
    """Return True if player meets Shaken Pressure conditions (HQ <= 7 or 2+ units lost this round)."""
    if player.hq_hp <= 7:
        return True
    lost = battlefield.p1_units_lost_this_round if player_idx == 0 else battlefield.p2_units_lost_this_round
    return lost >= 2


def maybe_mark_shaken_with_pressure(unit: BattleUnit, damage_taken: int,
                                     under_pressure: bool, log: list = None) -> bool:
    """Apply Shaken with reduced threshold (1 damage) when under pressure, else use normal 2 threshold."""
    if unit.is_dead:
        return False
    threshold = 1 if under_pressure else 2
    if damage_taken < threshold:
        return False
    if unit.current_hp * 2 > unit.base_max_hp:
        return False
    if not unit.mark_shaken():
        return False
    if log is not None:
        log.append(f"  ⚑ {unit.card.name} 动摇")
    return True


def effective_attack(unit: BattleUnit, battlefield: Battlefield, owner_idx: int) -> int:
    """计算单位在战场上下文中的实际攻击力，应用光环类关键词。

    应用规则：
    - 军团联动：当我方同槽位的炮兵处于 MAIN 或 SKIRMISH 时，骑兵 +1 攻
    - 死神威慑：每个处于此单位同槽位（任意线）的敌方"死神威慑"单位 -1 攻，最低为 0
    """
    atk = unit.card.attack

    if unit.card.unit_type == UnitType.CAVALRY:
        for line in (Line.MAIN, Line.SKIRMISH):
            for friendly in battlefield.get_line(owner_idx, line):
                if (friendly.slot == unit.slot
                        and friendly.card.unit_type == UnitType.ARTILLERY
                        and "军团联动" in friendly.card.keywords):
                    atk += 1
                    break

    enemy_idx = 1 - owner_idx
    intimidations = sum(
        1 for enemy in battlefield.all_units(enemy_idx)
        if enemy.slot == unit.slot and "死神威慑" in enemy.card.keywords
    )
    atk = max(0, atk - intimidations)

    # v0.3B: Imperial Guard sub-faction attack bonus
    if unit.card.subfaction and unit.card.subfaction.value == "imperial_guard":
        guard_count = sum(
            1 for u in battlefield.all_units(owner_idx)
            if u.card.subfaction and u.card.subfaction.value == "imperial_guard"
        )
        atk += min(guard_count, IMPERIAL_GUARD_ATK_CAP)

    if unit.is_shaken:
        atk = max(0, atk - 1)

    return atk


def attack_range(unit: BattleUnit) -> int:
    """返回单位在二维战场上的攻击距离。"""
    if unit.card.unit_type == UnitType.ARTILLERY:
        return 3
    if unit.card.unit_type == UnitType.SKIRMISHER:
        return 2
    if unit.card.unit_type == UnitType.CAVALRY:
        return 3 if "侧翼迂回" in unit.card.keywords else 1
    return 1


def _targets_in_range(
    battlefield: Battlefield,
    attacker: BattleUnit,
    attacker_player_idx: int,
    targets: List[BattleUnit],
) -> List[BattleUnit]:
    max_range = attack_range(attacker)
    return [
        target for target in targets
        if battlefield.distance(attacker_player_idx, attacker, target) <= max_range
    ]


def calculate_damage(
    attacker: BattleUnit,
    defender: BattleUnit,
    attacker_attack_override: Optional[int] = None,
    defender_attack_override: Optional[int] = None,
) -> Tuple[int, int]:
    """计算战斗伤害：返回 (defender 受到的伤害, attacker 受到的反击伤害)

    克制规则：
    - 骑兵冲锋打非方阵步兵：双倍伤害
    - 方阵步兵被骑兵打：伤害减半
    - 炮兵打方阵 / 密集步兵：伤害+1
    - 散兵带闪避：免疫第一次非炮兵攻击
    - 远程单位（炮兵）：不吃反击

    attacker_attack_override：传入则替代基础攻击力（用于光环类如 军团联动 / 死神威慑）。
    """
    a_card = attacker.card
    d_card = defender.card

    # 散兵闪避（一次性）
    if "闪避" in d_card.keywords and not defender.has_used_evade:
        if a_card.unit_type != UnitType.ARTILLERY:
            defender.has_used_evade = True
            return (0, 0)  # 完全闪避

    base_attack = attacker_attack_override if attacker_attack_override is not None else a_card.attack
    damage_to_defender = base_attack
    
    # === 骑兵 vs 步兵 ===
    if a_card.unit_type == UnitType.CAVALRY and d_card.unit_type in (UnitType.INFANTRY, UnitType.GUARD):
        if "结阵" in d_card.keywords and "突破" not in a_card.keywords:
            # 方阵抗骑兵；带"突破"的重骑兵无视方阵减伤
            damage_to_defender = max(1, base_attack // 2)
        else:
            # 散开的步兵被骑兵冲垮，或重骑兵突破方阵
            damage_to_defender = base_attack * 2 if "结阵" not in d_card.keywords else base_attack

    # === 炮兵 vs 密集步兵 ===
    if a_card.unit_type == UnitType.ARTILLERY and d_card.unit_type in (UnitType.INFANTRY, UnitType.GUARD):
        # 方阵步兵被炮弹横扫吃额外伤害
        if "结阵" in d_card.keywords:
            damage_to_defender = base_attack + 2
        else:
            damage_to_defender = base_attack + 1
    
    # === 齐射：本回合首次进攻 +1 伤害 ===
    if "齐射" in a_card.keywords and not attacker.has_acted_this_turn:
        damage_to_defender += 1

    # === 伤害减免（阿尔科莱精神）===
    if defender.damage_reduction_turns > 0:
        damage_to_defender = min(damage_to_defender, 1)

    # === 反击伤害 ===
    defender_attack = defender_attack_override if defender_attack_override is not None else d_card.attack
    if a_card.unit_type == UnitType.ARTILLERY and "远程" in a_card.keywords:
        damage_to_attacker = 0  # 远程炮兵不吃反击
    elif d_card.unit_type == UnitType.ARTILLERY:
        damage_to_attacker = max(0, defender_attack // 2)
    else:
        damage_to_attacker = defender_attack
    
    return (damage_to_defender, damage_to_attacker)


def calculate_damage_with_situation(
    attacker: BattleUnit,
    defender: BattleUnit,
    battlefield: Battlefield,
    attacker_attack_override: Optional[int] = None,
    defender_attack_override: Optional[int] = None,
    cannon_smoke_suppresses_qishe: bool = False,
    synergy_bonus: int = 0,
) -> Tuple[int, int]:
    """calculate_damage with battlefield situation modifiers applied.

    Modifier order: base → keyword → situation → synergy → evasion → final.
    """
    # Step 1-2: Get base damage with keywords
    dmg_def, dmg_atk = calculate_damage(
        attacker, defender,
        attacker_attack_override=attacker_attack_override,
        defender_attack_override=defender_attack_override,
    )

    # If evasion triggered (returned 0,0), don't modify further
    if dmg_def == 0 and dmg_atk == 0 and "闪避" in defender.card.keywords:
        return (0, 0)

    # Step 3: Cannon Smoke suppresses 齐射 on first attack this action
    if cannon_smoke_suppresses_qishe and "齐射" in attacker.card.keywords:
        # The 齐射 bonus was +1 in calculate_damage for units that haven't acted
        # Since the caller tracks attacks_this_action separately from has_acted_this_turn,
        # we check: if attacker hasn't acted yet AND cannon_smoke is active, remove 齐射 bonus
        if not attacker.has_acted_this_turn:
            dmg_def = max(0, dmg_def - 1)

    # Step 3 continued: Dense Fog reduces ranged damage
    if battlefield.current_situation_id == "dense_fog":
        if "远程" in attacker.card.keywords and dmg_def > 0:
            dmg_def = max(1, dmg_def - 1)

    # Step 4: Synergy bonuses
    if synergy_bonus > 0:
        dmg_def += synergy_bonus

    return (dmg_def, dmg_atk)


def is_cannon_smoke_suppressed(battlefield: Battlefield, attacks_this_action: int) -> bool:
    """Return True if Cannon Smoke should suppress 齐射 for this attack."""
    return battlefield.current_situation_id == "cannon_smoke" and attacks_this_action == 0


def apply_synergy_bonus(
    attacker: BattleUnit, defender: BattleUnit,
    battlefield: Battlefield, attacker_player_idx: int,
) -> int:
    """Return total synergy damage bonus for this attack. Max 1 synergy bonus per attack."""
    # Infantry + Artillery: artillery gets +1 vs units if infantry in same slot
    if attacker.card.unit_type == UnitType.ARTILLERY:
        for line in (Line.REAR, Line.MAIN):
            for friendly in battlefield.get_line(attacker_player_idx, line):
                if (friendly.slot == attacker.slot
                        and friendly.card.unit_type == UnitType.INFANTRY):
                    return 1

    # Cavalry vs Shaken: +1 damage
    if attacker.card.unit_type == UnitType.CAVALRY and defender.is_shaken:
        return 1

    return 0


def find_attack_targets(
    battlefield: Battlefield,
    attacker: BattleUnit,
    attacker_player_idx: int
) -> List[BattleUnit]:
    """找出 attacker 可以攻击的所有合法目标
    
    规则优先级：
    1. 守卫优先：敌方场上有守卫单位时，必须先打守卫
    2. 二维距离：每个单位按 row + slot 的曼哈顿距离筛选目标
    3. 远程：后方炮兵可以攻击距离内的散兵线和主力线，不能攻击对方后方
    4. 正面优先：优先攻击敌方散兵线，其次主力线
    """
    opp_idx = 1 - attacker_player_idx
    
    # 守卫单位（必须先打）
    guards_in_main = [u for u in battlefield.get_line(opp_idx, Line.MAIN) 
                      if "守卫" in u.card.keywords]
    guards_in_range = _targets_in_range(battlefield, attacker, attacker_player_idx, guards_in_main)
    
    # 远程炮兵（在后方线）：可以打散兵线和主力线，不能攻击对方后方。
    if (attacker.current_line == Line.REAR
        and "远程" in attacker.card.keywords
        and attacker.card.unit_type == UnitType.ARTILLERY):
        if guards_in_range:
            return guards_in_range
        targets = (battlefield.get_line(opp_idx, Line.SKIRMISH)
                   + battlefield.get_line(opp_idx, Line.MAIN))
        return _targets_in_range(battlefield, attacker, attacker_player_idx, targets)

    # 阿尔科莱精神炮兵：在主力线或散兵线时，可攻击敌方所有单位（含后方）
    if ("阿尔科莱精神" in attacker.card.keywords
        and attacker.card.unit_type == UnitType.ARTILLERY
        and attacker.current_line in (Line.MAIN, Line.SKIRMISH)):
        if guards_in_range:
            return guards_in_range
        targets = (battlefield.get_line(opp_idx, Line.SKIRMISH)
                   + battlefield.get_line(opp_idx, Line.MAIN)
                   + battlefield.get_line(opp_idx, Line.REAR))
        return _targets_in_range(battlefield, attacker, attacker_player_idx, targets)
    
    if attacker.current_line == Line.REAR:
        return []
    
    if guards_in_range:
        return guards_in_range
    targets = (battlefield.get_line(opp_idx, Line.SKIRMISH)
               + battlefield.get_line(opp_idx, Line.MAIN))
    if attacker.card.unit_type == UnitType.CAVALRY and "侧翼迂回" in attacker.card.keywords:
        targets += battlefield.get_line(opp_idx, Line.REAR)
    return _targets_in_range(battlefield, attacker, attacker_player_idx, targets)
    


def can_attack_hq(
    battlefield: Battlefield,
    attacker: BattleUnit,
    attacker_player_idx: int
) -> bool:
    """攻击者能否直接打 HQ
    
    核心规则（防止首回合rush）：
    - 必须从散兵线发起 HQ 攻击（前压到位才能打 HQ）
    - 远程炮兵例外：可以从后方线打，但需要敌方散兵+主力都为空
    - 侧翼迂回骑兵在散兵线时可以无视主力打HQ（如果敌方散兵和主力都被解决）
    """
    opp_idx = 1 - attacker_player_idx
    opp_skirmish = battlefield.get_line(opp_idx, Line.SKIRMISH)
    opp_main = battlefield.get_line(opp_idx, Line.MAIN)
    opp_rear = battlefield.get_line(opp_idx, Line.REAR)
    
    # 远程炮兵：敌方散兵+主力都为空时可以炮击 HQ
    if (attacker.current_line == Line.REAR
        and "远程" in attacker.card.keywords):
        return len(opp_skirmish) == 0 and len(opp_main) == 0

    # 阿尔科莱精神炮兵在主力线：敌方散兵+主力都为空时可打 HQ
    if ("阿尔科莱精神" in attacker.card.keywords
        and attacker.current_line == Line.MAIN):
        return len(opp_skirmish) == 0 and len(opp_main) == 0
    
    # 散兵线发起的攻击：敌方散兵线+主力线为空
    if attacker.current_line == Line.SKIRMISH:
        return len(opp_skirmish) == 0 and len(opp_main) == 0
    
    # 主力线/后方的非远程单位：不能直接打 HQ（必须先前压）
    return False


def execute_attack(
    attacker: BattleUnit,
    defender: BattleUnit,
    log: list = None,
    battlefield: Optional[Battlefield] = None,
    attacker_player_idx: Optional[int] = None,
    attack_bonus: int = 0,
    cannon_smoke_suppresses_qishe: bool = False,
    enable_unit_synergies: bool = False,
    under_pressure: bool = False,
) -> dict:
    """执行一次攻击，返回结算结果。

    若提供 battlefield 与 attacker_player_idx，则会应用光环类关键词
    （军团联动 / 死神威慑）到双方的有效攻击力。
    """
    synergy_bonus = 0
    if enable_unit_synergies and battlefield is not None and attacker_player_idx is not None:
        synergy_bonus = apply_synergy_bonus(attacker, defender, battlefield, attacker_player_idx)

    if battlefield is not None and attacker_player_idx is not None:
        attacker_atk = effective_attack(attacker, battlefield, attacker_player_idx) + attack_bonus
        defender_atk = effective_attack(defender, battlefield, 1 - attacker_player_idx)
        if battlefield.current_situation_id or synergy_bonus > 0:
            dmg_def, dmg_atk = calculate_damage_with_situation(
                attacker, defender, battlefield,
                attacker_attack_override=attacker_atk,
                defender_attack_override=defender_atk,
                cannon_smoke_suppresses_qishe=cannon_smoke_suppresses_qishe,
                synergy_bonus=synergy_bonus,
            )
        else:
            dmg_def, dmg_atk = calculate_damage(
                attacker, defender,
                attacker_attack_override=attacker_atk,
                defender_attack_override=defender_atk,
            )
    else:
        dmg_def, dmg_atk = calculate_damage(attacker, defender)

    defender.current_hp -= dmg_def
    attacker.current_hp -= dmg_atk
    attacker.has_acted_this_turn = True

    if under_pressure:
        maybe_mark_shaken_with_pressure(defender, dmg_def, under_pressure, log)
        maybe_mark_shaken_with_pressure(attacker, dmg_atk, under_pressure, log)
    else:
        maybe_mark_shaken(defender, dmg_def, log)
        maybe_mark_shaken(attacker, dmg_atk, log)

    # v0.3B: On Wounded trigger — fires when current_hp drops below base_max_hp
    if dmg_def > 0 and defender.current_hp > 0 and not defender.on_wounded_exhausted:
        if defender.current_hp < defender.base_max_hp:
            defender.on_wounded_exhausted = True

    # v0.5: Track damage modifiers for export metadata
    damage_modifiers = []
    if synergy_bonus > 0:
        synergy_id = "infantry_artillery" if attacker.card.unit_type == UnitType.ARTILLERY else "cavalry_pursuit"
        damage_modifiers.append({"source": "synergy", "id": synergy_id, "delta": synergy_bonus})

    result = {
        "attacker": attacker.card.name,
        "defender": defender.card.name,
        "dmg_to_defender": dmg_def,
        "dmg_to_attacker": dmg_atk,
        "defender_killed": defender.current_hp <= 0,
        "attacker_killed": attacker.current_hp <= 0,
        "smash_overflow": 0,
        "attacker_pos": {"line": attacker.current_line.value, "slot": attacker.slot},
        "defender_pos": {"line": defender.current_line.value, "slot": defender.slot},
        "defender_hp_after": max(0, defender.current_hp),
        "attacker_hp_after": max(0, attacker.current_hp),
        "damage_modifiers": damage_modifiers,
    }
    
    # 突破：杀死目标后溢出伤害打 HQ
    if "突破" in attacker.card.keywords and defender.current_hp <= 0:
        overflow = abs(defender.current_hp)  # 负数取绝对值
        if overflow > 0:
            result["smash_overflow"] = overflow
    
    if log is not None:
        log.append(
            f"  ⚔ {attacker.card.name}({attacker.current_hp + dmg_atk}hp) → "
            f"{defender.card.name}: 造成{dmg_def}伤害"
            + (f"，反击{dmg_atk}" if dmg_atk > 0 else "")
            + (f"，目标阵亡：{defender.card.name}" if result["defender_killed"] else "")
            + (f"，突破溢出{result['smash_overflow']}打HQ" if result["smash_overflow"] else "")
        )
    
    return result
