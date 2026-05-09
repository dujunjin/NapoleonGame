"""Commander definitions for v0.3A command layer."""

from dataclasses import dataclass
from enum import Enum
from cards import Faction


class CommanderId(Enum):
    NAPOLEON = "napoleon"
    BLUCHER = "blucher"
    KUTUZOV = "kutuzov"


@dataclass(frozen=True)
class Commander:
    id: CommanderId
    name: str
    faction: Faction
    ability_name: str
    description: str
    uses_per_match: int = 1
    enters_deck: bool = False


COMMANDERS = {
    CommanderId.NAPOLEON: Commander(
        id=CommanderId.NAPOLEON,
        name="拿破仑",
        faction=Faction.FRANCE,
        ability_name="Imperial Breakthrough",
        description="本回合一条友方战线的首次 HQ 直击 +1。",
    ),
    CommanderId.BLUCHER: Commander(
        id=CommanderId.BLUCHER,
        name="布吕歇尔",
        faction=Faction.PRUSSIA,
        ability_name="Counterstroke",
        description="本回合受伤友军攻击 +1。",
    ),
    CommanderId.KUTUZOV: Commander(
        id=CommanderId.KUTUZOV,
        name="库图佐夫",
        faction=Faction.RUSSIA,
        ability_name="Strategic Withdrawal",
        description="撤回一个非后方线友军，治疗 1，并恢复 HQ 1。",
    ),
}


DEFAULT_COMMANDERS = {
    Faction.FRANCE: CommanderId.NAPOLEON,
    Faction.PRUSSIA: CommanderId.BLUCHER,
    Faction.RUSSIA: CommanderId.KUTUZOV,
}


@dataclass(frozen=True)
class CommanderReaction:
    id: str
    trigger: str  # "hq_damage", "main_line_empty", "hq_damaged"
    description: str


COMMANDER_REACTIONS = {
    CommanderId.NAPOLEON: CommanderReaction(
        id="opportunity_seized",
        trigger="hq_damage",
        description="首次造成 HQ 伤害时，+1 军令",
    ),
    CommanderId.BLUCHER: CommanderReaction(
        id="rally_militia",
        trigger="main_line_empty",
        description="首次主力线被清空时，后方生成 1/2 后备国民军",
    ),
    CommanderId.KUTUZOV: CommanderReaction(
        id="strategic_retreat",
        trigger="hq_damaged",
        description="首次 HQ 受伤时，治疗最受伤友军 1 HP",
    ),
}


def get_default_commander(faction: Faction) -> Commander:
    return COMMANDERS[DEFAULT_COMMANDERS[faction]]
