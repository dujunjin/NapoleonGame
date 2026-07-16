#!/usr/bin/env python3
"""Export the canonical Python decks into the Unity vertical-slice catalog."""

from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "prototypes" / "card-battle-sim"
OUTPUT = ROOT / "src" / "NapoleonGame.Unity" / "Assets" / "NapoleonGame" / "Data" / "card_catalog.json"
sys.path.insert(0, str(SIM))

from cards import CardType, Faction, UnitType, DECK_BUILDERS  # noqa: E402


FACTION_META = {
    Faction.FRANCE: ("france", "fr", "法兰西", "napoleon", "拿破仑"),
    Faction.PRUSSIA: ("prussia", "pr", "普鲁士", "blucher", "布吕歇尔"),
    Faction.RUSSIA: ("russia", "ru", "俄罗斯", "kutuzov", "库图佐夫"),
}

KEYWORD_TEXT = {
    "冲锋": "部署回合即可行动。",
    "结阵": "降低未突破骑兵的冲击伤害。",
    "齐射": "首次攻击前额外造成1点伤害。",
    "远程": "可从支援线远程攻击且不受反击。",
    "闪避": "首次受到非炮兵攻击时免疫伤害。",
    "突破": "击毁单位后将溢出伤害施加给敌方HQ。",
    "守卫": "同区域存在守卫时，敌军必须优先攻击守卫。",
    "侧翼迂回": "可从支援线攻击敌方支援单位。",
    "阿尔科莱精神": "进入前线后攻击力+2。",
    "军团联动": "与友军骑兵协同时提供攻击加成。",
    "死神威慑": "压低同槽位敌军攻击力。",
    "熔岩战术": "攻击后若存活则撤回支援线。",
    "焦土补给": "阵亡后为拥有者提供下回合补给。",
}

EVENT_TEXT = {
    "buff_target_INF+1+2": "一个友军步兵永久+1攻击、+2生命并治疗2。",
    "advance_friendly_one_no_attack": "一个未动摇友军免费进入前线，但不能立刻攻击。",
    "fortify_target_INF_GUARD+0+2_guard": "一个友军步兵或近卫+2生命、治疗2并获得守卫。",
    "draw1_buff_target_INF+1+1": "抽1张牌；一个友军步兵+1/+1并治疗1。",
    "buff_all_friendly_CAV_GUARD+1": "所有友军骑兵与近卫永久+1攻击。",
    "retreat_friendly_heal2_hq1": "一个前线友军撤回支援并治疗2；己方HQ受到1点伤害。",
    "self_hq1_damage_enemy_skirmish1": "己方HQ受到1点伤害；敌方前线单位各受到1点伤害。",
    "weather_fog_artillery-1": "全场炮兵永久-1攻击。",
    "weather_mud_cavalry-1": "全场骑兵永久-1攻击。",
    "weather_winter_all_damage1": "全场所有单位受到1点伤害。",
    "buff_imperial_guard_deploy_sequence": "强化一个帝国近卫；本回合已部署步兵时额外抽1张牌。",
    "buff_landwehr_sequence": "强化一个国土后备军；本回合已部署后备军时额外抽1张牌。",
    "buff_cossack_death_extend": "本回合下一个阵亡的哥萨克返还其行动费用。",
}


def operation_cost(card) -> int:
    if card.card_type == CardType.EVENT:
        return 0
    if card.unit_type in (UnitType.INFANTRY, UnitType.SKIRMISHER):
        return 1
    return 2


def rules_text(card) -> str:
    if card.card_type == CardType.EVENT:
        return EVENT_TEXT.get(card.event_effect or "", "按卡牌描述结算一次性战术效果。")
    parts = []
    for keyword in card.keywords:
        if keyword.startswith("自残"):
            parts.append(f"部署：己方HQ受到{keyword.removeprefix('自残')}点伤害。")
        elif keyword == "光环+1攻":
            parts.append("部署：其他友军永久+1攻击。")
        elif keyword == "光环+1血":
            parts.append("部署：其他友军永久+1生命。")
        elif keyword in KEYWORD_TEXT:
            parts.append(KEYWORD_TEXT[keyword])
    return "".join(parts) or "无额外能力。"


def export_faction(faction: Faction) -> dict:
    faction_id, prefix, display_name, commander_id, commander_name = FACTION_META[faction]
    grouped: OrderedDict[str, dict] = OrderedDict()
    for card in DECK_BUILDERS[faction]():
        if card.name not in grouped:
            index = len(grouped) + 1
            grouped[card.name] = {
                "id": f"{prefix}-{index:02d}",
                "name": card.name,
                "faction": faction_id,
                "cardType": card.card_type.value,
                "unitType": card.unit_type.name.lower(),
                "deployCost": card.cost,
                "operationCost": operation_cost(card),
                "attack": card.attack,
                "health": card.health,
                "keywords": list(card.keywords),
                "eventEffect": card.event_effect or "",
                "subfaction": card.subfaction.value if card.subfaction else "",
                "quantity": 0,
                "rulesText": rules_text(card),
                "artKey": f"{faction_id}_{card.unit_type.name.lower() if card.card_type == CardType.UNIT else 'event'}",
            }
        grouped[card.name]["quantity"] += 1

    cards = list(grouped.values())
    deck_size = sum(card["quantity"] for card in cards)
    if deck_size != 33:
        raise RuntimeError(f"{display_name} deck size is {deck_size}, expected 33")

    return {
        "id": faction_id,
        "displayName": display_name,
        "commanderId": commander_id,
        "commanderName": commander_name,
        "deckSize": deck_size,
        "cards": cards,
    }


def main() -> None:
    payload = {
        "schemaVersion": 1,
        "generatedFrom": "prototypes/card-battle-sim/cards.py",
        "factions": [export_faction(faction) for faction in Faction],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    for faction in payload["factions"]:
        print(f"{faction['displayName']}: {faction['deckSize']} cards, {len(faction['cards'])} definitions")


if __name__ == "__main__":
    main()

