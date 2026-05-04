"""
拿破仑卡牌游戏规则模拟器 - 战斗系统

核心规则：
1. 兵种克制：通过关键词 + 类型判断动态计算伤害
2. 目标选择：优先散兵线 → 主力线 → 后方
3. 守卫：场上有守卫单位时必须先打守卫
4. 侧翼迂回：散兵线的轻骑兵可以无视守卫直击后方炮兵
"""

from typing import List, Optional, Tuple
from cards import Card, UnitType, Line
from game_state import BattleUnit, Battlefield


def calculate_damage(attacker: BattleUnit, defender: BattleUnit) -> Tuple[int, int]:
    """计算战斗伤害：返回 (defender 受到的伤害, attacker 受到的反击伤害)
    
    克制规则：
    - 骑兵冲锋打非方阵步兵：双倍伤害
    - 方阵步兵被骑兵打：伤害减半
    - 炮兵打方阵 / 密集步兵：伤害+1
    - 散兵带闪避：免疫第一次非炮兵攻击
    - 远程单位（炮兵）：不吃反击
    """
    a_card = attacker.card
    d_card = defender.card
    
    # 散兵闪避（一次性）
    if "闪避" in d_card.keywords and not defender.has_used_evade:
        if a_card.unit_type != UnitType.ARTILLERY:
            defender.has_used_evade = True
            return (0, 0)  # 完全闪避
    
    base_attack = a_card.attack
    damage_to_defender = base_attack
    
    # === 骑兵 vs 步兵 ===
    if a_card.unit_type == UnitType.CAVALRY and d_card.unit_type in (UnitType.INFANTRY, UnitType.GUARD):
        if "结阵" in d_card.keywords:
            # 方阵抗骑兵
            damage_to_defender = max(1, base_attack // 2)
        else:
            # 散开的步兵被骑兵冲垮
            damage_to_defender = base_attack * 2
    
    # === 炮兵 vs 密集步兵 ===
    if a_card.unit_type == UnitType.ARTILLERY and d_card.unit_type in (UnitType.INFANTRY, UnitType.GUARD):
        damage_to_defender = base_attack + 1
    
    # === 齐射先制 ===
    pre_strike_damage = 0
    if "齐射" in a_card.keywords:
        pre_strike_damage = 1
    
    damage_to_defender += pre_strike_damage
    
    # === 反击伤害 ===
    if a_card.unit_type == UnitType.ARTILLERY and "远程" in a_card.keywords:
        damage_to_attacker = 0  # 远程炮兵不吃反击
    elif d_card.unit_type == UnitType.ARTILLERY:
        # 攻击炮兵不吃反击（炮兵被冲了基本是单方面挨打）
        damage_to_attacker = max(0, d_card.attack // 2)
    else:
        damage_to_attacker = d_card.attack
        # 方阵反骑兵
        if "结阵" in d_card.keywords and a_card.unit_type == UnitType.CAVALRY:
            damage_to_attacker = d_card.attack  # 全额反击
    
    return (damage_to_defender, damage_to_attacker)


def find_attack_targets(
    battlefield: Battlefield,
    attacker: BattleUnit,
    attacker_player_idx: int
) -> List[BattleUnit]:
    """找出 attacker 可以攻击的所有合法目标
    
    规则优先级：
    1. 守卫优先：敌方场上有守卫单位时，必须先打守卫
    2. 侧翼迂回：散兵线的骑兵带"侧翼迂回"，可以无视主力线直击后方炮兵
    3. 远程：后方炮兵可以攻击散兵线和主力线（不能攻击对方后方）
    4. 散兵线：在散兵线的单位攻击敌方散兵线和敌方主力线
    5. 主力线：在主力线的单位优先攻击散兵线（如果有），否则攻击敌方主力线
    """
    opp_idx = 1 - attacker_player_idx
    
    # 守卫单位（必须先打）
    guards_in_main = [u for u in battlefield.get_line(opp_idx, Line.MAIN) 
                      if "守卫" in u.card.keywords]
    
    # 侧翼迂回（在散兵线的骑兵）
    if (attacker.current_line == Line.SKIRMISH 
        and "侧翼迂回" in attacker.card.keywords
        and attacker.card.unit_type == UnitType.CAVALRY):
        # 后方炮兵优先目标
        rear_artillery = [u for u in battlefield.get_line(opp_idx, Line.REAR)]
        if rear_artillery:
            return rear_artillery
    
    # 远程炮兵（在后方线）
    if (attacker.current_line == Line.REAR 
        and "远程" in attacker.card.keywords
        and attacker.card.unit_type == UnitType.ARTILLERY):
        # 可以打散兵线和主力线
        if guards_in_main:
            return guards_in_main
        targets = (battlefield.get_line(opp_idx, Line.SKIRMISH) 
                   + battlefield.get_line(opp_idx, Line.MAIN))
        return targets
    
    # 散兵线单位
    if attacker.current_line == Line.SKIRMISH:
        # 优先打敌方散兵线
        opp_skirmish = battlefield.get_line(opp_idx, Line.SKIRMISH)
        if opp_skirmish:
            return opp_skirmish
        if guards_in_main:
            return guards_in_main
        return battlefield.get_line(opp_idx, Line.MAIN)
    
    # 主力线单位
    if attacker.current_line == Line.MAIN:
        # 必须先解决敌方散兵线
        opp_skirmish = battlefield.get_line(opp_idx, Line.SKIRMISH)
        if opp_skirmish:
            return opp_skirmish
        if guards_in_main:
            return guards_in_main
        return battlefield.get_line(opp_idx, Line.MAIN)
    
    return []


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
    
    # 散兵线发起的攻击：敌方散兵线+主力线为空
    if attacker.current_line == Line.SKIRMISH:
        return len(opp_skirmish) == 0 and len(opp_main) == 0
    
    # 主力线/后方的非远程单位：不能直接打 HQ（必须先前压）
    return False


def execute_attack(
    attacker: BattleUnit,
    defender: BattleUnit,
    log: list = None
) -> dict:
    """执行一次攻击，返回结算结果"""
    dmg_def, dmg_atk = calculate_damage(attacker, defender)
    
    defender.current_hp -= dmg_def
    attacker.current_hp -= dmg_atk
    attacker.has_acted_this_turn = True
    
    result = {
        "attacker": attacker.card.name,
        "defender": defender.card.name,
        "dmg_to_defender": dmg_def,
        "dmg_to_attacker": dmg_atk,
        "defender_killed": defender.current_hp <= 0,
        "attacker_killed": attacker.current_hp <= 0,
        "smash_overflow": 0,
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
