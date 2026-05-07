"""
拿破仑卡牌游戏规则模拟器 - v0.3B 触发系统

触发类型（7种）：
- On Deploy, On Advance, On Attack, On Wounded, On Destroy
- Same-line Threshold, Sequence
"""

from enum import Enum
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cards import Card
    from game_state import BattleUnit, Battlefield, Player


MAX_CHAIN_DEPTH = 4
IMPERIAL_GUARD_ATK_CAP = 3
LANDWEHR_HP_CAP = 3
COSSACK_REFUND_CAP_PER_TURN = 3


class TriggerType(Enum):
    ON_DEPLOY = "on_deploy"
    ON_ADVANCE = "on_advance"
    ON_ATTACK = "on_attack"
    ON_WOUNDED = "on_wounded"
    ON_DESTROY = "on_destroy"
    SAME_LINE_THRESHOLD = "same_line_threshold"
    SEQUENCE = "sequence"


# Mapping of legacy keywords to trigger types
LEGACY_TRIGGER_MAP = {
    "自残": TriggerType.ON_DEPLOY,
    "焦土补给": TriggerType.ON_DESTROY,
    "熔岩战术": TriggerType.ON_ATTACK,
    "阿尔科莱精神": TriggerType.ON_ADVANCE,
}


def count_trigger_types(card: "Card") -> int:
    """Count distinct trigger types on a card. Static modifiers and sub-faction tags don't count."""
    types = set()

    # Check legacy keywords
    for kw in card.keywords:
        for prefix, trigger_type in LEGACY_TRIGGER_MAP.items():
            if kw.startswith(prefix):
                types.add(trigger_type)

    # Check new v0.3B keywords
    new_keyword_map = {
        "On Deploy": TriggerType.ON_DEPLOY,
        "On Advance": TriggerType.ON_ADVANCE,
        "On Attack": TriggerType.ON_ATTACK,
        "On Wounded": TriggerType.ON_WOUNDED,
        "On Destroy": TriggerType.ON_DESTROY,
        "Same-line Threshold": TriggerType.SAME_LINE_THRESHOLD,
        "Sequence": TriggerType.SEQUENCE,
    }
    for kw in card.keywords:
        if kw in new_keyword_map:
            types.add(new_keyword_map[kw])

    return len(types)


def count_same_subfaction(battlefield: "Battlefield", player_idx: int,
                          subfaction: str, unit: "BattleUnit") -> int:
    """Count alive units with the same subfaction tag, including self."""
    count = 0
    for u in battlefield.all_units(player_idx):
        if u.card.subfaction and u.card.subfaction.value == subfaction:
            count += 1
    return count


def get_subfaction_bonus(unit: "BattleUnit", battlefield: "Battlefield",
                         player_idx: int) -> dict:
    """Calculate sub-faction in-play count bonus for a unit."""
    if not unit.card.subfaction:
        return {}

    tag = unit.card.subfaction.value
    count = count_same_subfaction(battlefield, player_idx, tag, unit)

    if tag == "imperial_guard":
        bonus = min(count, IMPERIAL_GUARD_ATK_CAP)
        return {"attack_bonus": bonus}
    elif tag == "landwehr":
        return {"max_hp_bonus": min(count, LANDWEHR_HP_CAP)}
    elif tag == "cossack":
        return {"cossack_count": count}
    return {}


def evaluate_same_line_threshold(battlefield: "Battlefield", player_idx: int,
                                  unit: "BattleUnit", min_count: int = 3,
                                  unit_type_filter: str = None) -> bool:
    """Check if Same-line Threshold condition is met."""
    line_units = battlefield.get_line(player_idx, unit.current_line)
    if unit_type_filter:
        count = sum(1 for u in line_units if u.card.unit_type.value == unit_type_filter)
    else:
        count = len(line_units)
    return count >= min_count


def evaluate_sequence(player: "Player", required_category: str,
                      current_card_name: str = None) -> bool:
    """Check if Sequence condition is met. Excludes the current card."""
    for entry in player.play_log:
        if current_card_name and entry.card_name == current_card_name:
            continue
        if required_category == "INFANTRY" and entry.unit_type == "线列步兵":
            return True
        if required_category == "CAVALRY" and entry.unit_type == "骑兵":
            return True
        if required_category == "ARTILLERY" and entry.unit_type == "炮兵":
            return True
        if required_category == "GUARD" and entry.unit_type == "近卫":
            return True
        if required_category == "EVENT" and entry.card_type == "event":
            return True
        # Sub-faction tag match
        if entry.subfaction == required_category:
            return True
        # Cost band match
        if required_category.startswith("cost>="):
            threshold = int(required_category.split(">=")[1])
            if entry.cost >= threshold:
                return True
    return False
