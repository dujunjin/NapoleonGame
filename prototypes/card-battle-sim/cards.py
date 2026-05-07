"""
拿破仑卡牌游戏规则模拟器 - 卡牌定义

设计原则：
- 数据驱动：所有卡牌都是数据，不是写死的逻辑
- 关键词系统：通过关键词组合表达兵种特性，避免一卡一逻辑
- 简化但保留拿战核心：步兵阵型、骑兵冲锋、炮兵远程、散兵骚扰
- 卡牌类型：UNIT（部署到战场）/ EVENT（一次性效果，不上场）
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class CardType(Enum):
    """卡牌大类"""
    UNIT = "unit"
    EVENT = "event"


class UnitType(Enum):
    """兵种类型"""
    INFANTRY = "线列步兵"      # 主力，结阵防骑兵
    CAVALRY = "骑兵"           # 高攻，冲锋，怕方阵
    ARTILLERY = "炮兵"         # 后方远程，怕骑兵突袭
    SKIRMISHER = "散兵"        # 前压骚扰，闪避
    GUARD = "近卫"             # 高数值精锐


class Line(Enum):
    """战场三线"""
    REAR = "后方线"        # 炮兵阵地，HQ 所在
    MAIN = "主力战列线"    # 步兵主战场
    SKIRMISH = "散兵线"    # 公共前压区，与对方共享


class Faction(Enum):
    """阵营"""
    FRANCE = "法兰西"
    PRUSSIA = "普鲁士"
    RUSSIA = "俄罗斯"


class SubFaction(Enum):
    """子阵营标签"""
    IMPERIAL_GUARD = "imperial_guard"   # 帝国近卫 (France)
    LANDWEHR = "landwehr"               # 国土后备军 (Prussia)
    COSSACK = "cossack"                 # 哥萨克 (Russia)


@dataclass
class Card:
    """卡牌定义。UNIT 卡使用 attack/health/unit_type/deploy_line；EVENT 卡使用 event_effect。"""
    name: str
    cost: int                      # 军令消耗
    attack: int
    health: int
    unit_type: UnitType
    faction: Faction
    deploy_line: Line              # 默认部署在哪条线
    keywords: List[str] = field(default_factory=list)
    card_type: CardType = CardType.UNIT
    event_effect: Optional[str] = None  # 仅 EVENT 卡使用，例如 "buff_target_INF+1+2"
    subfaction: Optional[SubFaction] = None  # 子阵营标签

    def __repr__(self):
        if self.card_type == CardType.EVENT:
            return f"{self.name}({self.cost}费 事件)"
        return f"{self.name}({self.cost}费 {self.attack}/{self.health})"


# ============================================================
# 关键词说明（在战斗系统里实现）：
# ============================================================
# "冲锋"      - 部署当回合可立即攻击
# "结阵"      - 受到骑兵攻击时伤害减半
# "齐射"      - 攻击前先造成 1 点先制伤害
# "远程"      - 攻击不受反击伤害，但只能从后方线攻击
# "闪避"      - 第一次受到非炮兵攻击时免疫
# "突破"      - 杀死目标后溢出伤害打 HQ
# "守卫"      - 强制敌方优先攻击此单位
# "侧翼迂回"  - 可跨线攻击敌方后方炮兵
# "阿尔科莱精神" - 炮兵可前压，到达散兵线时攻击力+2
#
# === 法兰西阵营 ===
# "军团联动"  - 我方同槽位骑兵在此炮兵处于 MAIN/SKIRMISH 时攻击力 +1
#
# === 普鲁士阵营 ===
# "死神威慑"  - 处于此单位同一槽位的敌人攻击力 -1（最低 0），多个来源叠加
#
# === 俄罗斯阵营 ===
# "自残N"    - 部署时对自己 HQ 造成 N 点伤害（代价）
# "光环+1攻" - 部署后，所有其他友军单位永久 +1 攻击力
# "光环+1血" - 部署后，所有其他友军单位永久 +1 血量上限
# "熔岩战术" - 此单位攻击结算后撤回 REAR；下回合可再次行动（哥萨克游击）
# "焦土补给" - 此单位死亡时，拥有者下一回合 max_orders +1（不超上限）
#
# === 事件卡效果 (event_effect) ===
# "buff_target_INF+1+2"           - 选择一个我方 INFANTRY，永久 +1/+2 并回血 2
# "advance_friendly_one_no_attack" - 选择一个友军单位前移一格（REAR→MAIN 优先），不触发攻击
# "fortify_target_INF_GUARD+0+2_guard" - 选择我方 INFANTRY/GUARD，+0/+2 回血 2，获得守卫
# "draw1_buff_target_INF+1+1"     - 抽 1 张牌，选择我方 INFANTRY +1/+1 回血 1
# "buff_all_friendly_CAV_GUARD+1" - 全场友军 CAVALRY/GUARD 永久 +1 攻
# "retreat_friendly_heal2_hq1"    - 选择友军非 REAR 单位撤回 REAR，回血 2，自损 HQ 1
# "self_hq1_damage_enemy_skirmish1" - 自损 HQ 1，敌方散兵线全体 -1 血
# "weather_fog_artillery-1"       - 全场炮兵永久 -1 攻（最低 0）
# "weather_mud_cavalry-1"         - 全场骑兵永久 -1 攻（最低 0）
# "weather_winter_all_damage1"    - 全场所有单位 -1 血


# ============================================================
# 法兰西阵营牌库（30 张）
# 风格：高攻击力、纵队冲锋、近卫精锐、军团联动
# ============================================================
def build_france_deck() -> List[Card]:
    deck = []

    # 散兵 ×2：低费骚扰（v0.3B: 3→2 为新卡腾位）
    for _ in range(2):
        deck.append(Card("猎兵连", 1, 1, 2, UnitType.SKIRMISHER, Faction.FRANCE,
                         Line.SKIRMISH, ["闪避"]))

    # 线列步兵 ×4：主力
    for _ in range(4):
        deck.append(Card("第45线列步兵团", 3, 3, 4, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵", "齐射"]))

    # === v0.3B 新卡 ===
    # 老近卫先遣营：Imperial Guard anchor, On Deploy synergy
    deck.append(Card("老近卫先遣营", 4, 3, 5, UnitType.INFANTRY, Faction.FRANCE,
                     Line.MAIN, ["结阵", "齐射", "On Deploy"],
                     subfaction=SubFaction.IMPERIAL_GUARD))

    # 侦察骑兵纵队：Sequence discount (INFANTRY → cheaper cavalry)
    deck.append(Card("侦察骑兵纵队", 3, 3, 3, UnitType.CAVALRY, Faction.FRANCE,
                     Line.MAIN, ["冲锋", "Sequence"]))

    # 老近卫掷弹兵：Imperial Guard carrier, high stats
    deck.append(Card("老近卫掷弹兵", 5, 5, 6, UnitType.GUARD, Faction.FRANCE,
                     Line.MAIN, ["守卫", "结阵"],
                     subfaction=SubFaction.IMPERIAL_GUARD))

    # 帝国传令官：EVENT with On Deploy + Sequence
    deck.append(Card("帝国传令官", 2, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, ["On Deploy", "Sequence"],
                     CardType.EVENT, "buff_imperial_guard_deploy_sequence",
                     subfaction=SubFaction.IMPERIAL_GUARD))

    # 高费精锐线列 ×3：法军核心
    for _ in range(3):
        deck.append(Card("近卫掷弹兵", 5, 5, 5, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵", "齐射", "守卫"],
                         subfaction=SubFaction.IMPERIAL_GUARD))

    # 龙骑兵 ×3：中费骑兵（攻击 4→3；与 军团联动 联动后回到 4 攻）
    for _ in range(3):
        deck.append(Card("龙骑兵团", 4, 3, 3, UnitType.CAVALRY, Faction.FRANCE,
                         Line.MAIN, ["冲锋"]))

    # 胸甲骑兵 ×1：高费重骑
    deck.append(Card("胸甲骑兵", 6, 6, 5, UnitType.CAVALRY, Faction.FRANCE,
                     Line.MAIN, ["冲锋", "突破"]))

    # 骑炮 ×2：机动炮兵 + 军团联动
    for _ in range(2):
        deck.append(Card("近卫马炮兵", 4, 3, 3, UnitType.ARTILLERY, Faction.FRANCE,
                         Line.REAR, ["远程", "阿尔科莱精神", "军团联动"],
                         subfaction=SubFaction.IMPERIAL_GUARD))

    # 重炮 ×2：高费后排炮（无 军团联动 — 重炮固定不机动，不能与骑兵协同）
    for _ in range(2):
        deck.append(Card("12磅野战炮", 5, 4, 3, UnitType.ARTILLERY, Faction.FRANCE,
                         Line.REAR, ["远程"]))

    # 老近卫 ×1：终极牌（攻击 7→6 削弱）
    deck.append(Card("老近卫军", 8, 6, 8, UnitType.GUARD, Faction.FRANCE,
                     Line.MAIN, ["结阵", "齐射", "守卫", "突破"],
                     subfaction=SubFaction.IMPERIAL_GUARD))

    # 轻骑兵 ×2：低费骑兵（v0.3B: 3→2 为新卡腾位）
    for _ in range(2):
        deck.append(Card("骠骑兵", 2, 2, 2, UnitType.CAVALRY, Faction.FRANCE,
                         Line.MAIN, ["冲锋", "侧翼迂回"]))

    # 步兵纵队 ×2：低费铺场步兵（v0.3B: 3→2 为新卡腾位）
    for _ in range(2):
        deck.append(Card("征召步兵营", 2, 2, 3, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵"]))

    # 大军步兵 ×3：中费铺场（v0.3B: 4→3 为新卡腾位）
    for _ in range(3):
        deck.append(Card("帝国步兵团", 4, 4, 4, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵", "齐射"]))

    # === 事件卡 ===
    deck.append(Card("达武的铁军", 2, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, [], CardType.EVENT, "fortify_target_INF_GUARD+0+2_guard"))
    deck.append(Card("奥斯特里茨晨雾", 2, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, [], CardType.EVENT, "weather_fog_artillery-1"))

    # === 扩展事件 / 将领卡 ===
    deck.append(Card("拿破仑的预备队", 4, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, [], CardType.EVENT, "fortify_target_INF_GUARD+0+2_guard"))
    deck.append(Card("军团传令", 3, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, [], CardType.EVENT, "advance_friendly_one_no_attack"))

    return deck


# ============================================================
# 普鲁士阵营牌库（30 张）
# 风格：死神威慑 + 国防动员事件 + 改良线列
# ============================================================
def build_prussia_deck() -> List[Card]:
    deck = []

    # 散兵 ×2：普鲁士军事改革核心（v0.3B: 3→2 为新卡腾位）
    for _ in range(2):
        deck.append(Card("耶格猎兵", 1, 2, 2, UnitType.SKIRMISHER, Faction.PRUSSIA,
                         Line.SKIRMISH, ["闪避", "齐射"]))

    # 国民军 ×6：低费铺场步兵
    for _ in range(6):
        deck.append(Card("西里西亚国民军", 2, 2, 3, UnitType.INFANTRY, Faction.PRUSSIA,
                         Line.MAIN, ["结阵"]))

    # 线列步兵 ×4：攻击 3→4 微调（弥补普军输出弱）
    for _ in range(4):
        deck.append(Card("普鲁士线列军", 3, 4, 4, UnitType.INFANTRY, Faction.PRUSSIA,
                         Line.MAIN, ["结阵", "齐射"]))

    # 掷弹兵 ×3：精锐步兵
    for _ in range(3):
        deck.append(Card("近卫掷弹兵团", 4, 4, 5, UnitType.INFANTRY, Faction.PRUSSIA,
                         Line.MAIN, ["结阵", "齐射", "守卫"]))

    # 死神骠骑兵 ×3：低费骑兵 + 死神威慑
    for _ in range(3):
        deck.append(Card("死骑兵", 2, 2, 2, UnitType.CAVALRY, Faction.PRUSSIA,
                         Line.MAIN, ["冲锋", "死神威慑"]))

    # 龙骑兵 ×2
    for _ in range(2):
        deck.append(Card("普鲁士龙骑", 4, 4, 3, UnitType.CAVALRY, Faction.PRUSSIA,
                         Line.MAIN, ["冲锋"]))

    # 重炮 ×2
    for _ in range(2):
        deck.append(Card("普鲁士重炮", 5, 5, 3, UnitType.ARTILLERY, Faction.PRUSSIA,
                         Line.REAR, ["远程"]))

    # 黑色布伦瑞克军 ×1：精锐 + 死神威慑（v0.3B: 2→1 为新卡腾位）
    deck.append(Card("黑色布伦瑞克", 5, 5, 4, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.MAIN, ["结阵", "突破", "死神威慑"]))

    # 元帅近卫 ×1：高数值（v0.3B: 2→1 为新卡腾位）
    deck.append(Card("布吕歇尔的近卫", 6, 6, 6, UnitType.GUARD, Faction.PRUSSIA,
                     Line.MAIN, ["结阵", "守卫"]))

    # 国防动员 ×2：事件卡 — 选择一个我方 INFANTRY，永久 +1/+2 并回血 2（cost 3→2 加强普军 tempo）
    for _ in range(2):
        deck.append(Card(
            name="国防动员", cost=2,
            attack=0, health=0,
            unit_type=UnitType.INFANTRY,  # 占位，事件卡不上场
            faction=Faction.PRUSSIA,
            deploy_line=Line.REAR,        # 占位
            keywords=[],
            card_type=CardType.EVENT,
            event_effect="buff_target_INF+1+2",
        ))

    # 沙恩霍斯特改革：抽 1 张牌，选择我方 INFANTRY +1/+1 回血 1
    deck.append(Card("沙恩霍斯特改革", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "draw1_buff_target_INF+1+1"))
    # 布吕歇尔的追击令：全场友军 CAVALRY/GUARD +1 攻
    deck.append(Card("布吕歇尔的追击令", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "buff_all_friendly_CAV_GUARD+1"))
    # 莱比锡泥泞：全场骑兵永久 -1 攻
    deck.append(Card("莱比锡泥泞", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "weather_mud_cavalry-1"))

    # === v0.3B 新卡 ===
    # 勃兰登堡后备营：Landwehr anchor, On Wounded identity
    deck.append(Card("勃兰登堡后备营", 3, 3, 4, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.MAIN, ["结阵", "On Wounded"],
                     subfaction=SubFaction.LANDWEHR))

    # 反冲击突击队：On Attack with discipline condition (while wounded)
    deck.append(Card("反冲击突击队", 4, 4, 4, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.MAIN, ["结阵", "齐射", "死神威慑", "On Attack"]))

    # 西里西亚国民军线列：Landwehr + Same-line Threshold
    deck.append(Card("西里西亚国民军线列", 2, 2, 3, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.MAIN, ["结阵", "Same-line Threshold"],
                     subfaction=SubFaction.LANDWEHR))

    # 沙恩霍斯特参谋长：EVENT with Sequence (Landwehr → buff)
    deck.append(Card("沙恩霍斯特参谋长", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, ["Sequence"],
                     CardType.EVENT, "buff_landwehr_sequence"))

    return deck


# ============================================================
# 俄罗斯阵营牌库（30 张）
# 风格：低费铺场 + HQ 自残换效果 + 哥萨克熔岩战术 + 焦土补给
# 核心定位：消耗战、肉盾耐打、靠后期光环和侧翼威胁取胜
# ============================================================
def build_russia_deck() -> List[Card]:
    deck = []

    # 哥萨克轻骑 ×2：低费骚扰骑兵 + 熔岩战术（cavalry-to-skirmish AI 让 1 费过强，回到 2 费 2/2）
    for _ in range(2):
        deck.append(Card("哥萨克轻骑", 2, 2, 2, UnitType.CAVALRY, Faction.RUSSIA,
                         Line.MAIN, ["冲锋", "侧翼迂回", "熔岩战术"],
                         subfaction=SubFaction.COSSACK))

    # 俄军猎兵团 ×1：占据散兵线的低费散兵（v0.3B: 2→1 为新卡腾位）
    for _ in range(1):
        deck.append(Card("俄军猎兵团", 1, 1, 2, UnitType.SKIRMISHER, Faction.RUSSIA,
                         Line.SKIRMISH, ["闪避"]))

    # 东正教民兵 ×2：超低费铺场 + 焦土补给（v0.3B: 3→2 为新卡腾位）
    for _ in range(2):
        deck.append(Card("东正教民兵", 2, 2, 3, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵", "焦土补给"]))

    # 俄国线列军 ×4：保留 2/5 肉盾（与原版一致）
    for _ in range(4):
        deck.append(Card("俄国线列军", 3, 2, 5, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵"]))

    # 步兵炮 ×1：基础炮兵（v0.3B: 2→1 为新卡腾位）
    for _ in range(1):
        deck.append(Card("俄军步兵炮", 3, 3, 2, UnitType.ARTILLERY, Faction.RUSSIA,
                         Line.REAR, ["远程"]))

    # 西伯利亚老兵 ×2：自残 1，超模数值（不变）
    for _ in range(2):
        deck.append(Card("西伯利亚老兵", 3, 5, 5, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵", "自残1"]))

    # 普拉托夫的哥萨克 ×2：高数值侧翼骑兵 + 熔岩战术
    for _ in range(2):
        deck.append(Card("普拉托夫的哥萨克", 4, 3, 2, UnitType.CAVALRY, Faction.RUSSIA,
                         Line.MAIN, ["冲锋", "侧翼迂回", "熔岩战术"],
                         subfaction=SubFaction.COSSACK))

    # 龙骑兵 ×1：标准骑兵（v0.3B: 2→1 为新卡腾位）
    for _ in range(1):
        deck.append(Card("俄军龙骑", 4, 4, 3, UnitType.CAVALRY, Faction.RUSSIA,
                         Line.MAIN, ["冲锋"]))

    # 莫斯科掷弹兵 ×2：中费精锐
    for _ in range(2):
        deck.append(Card("莫斯科掷弹兵", 5, 4, 5, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵", "守卫"]))

    # 独角兽榴弹炮 ×2：重型炮
    for _ in range(2):
        deck.append(Card("独角兽榴弹炮", 5, 5, 3, UnitType.ARTILLERY, Faction.RUSSIA,
                         Line.REAR, ["远程"]))

    # 巴格拉季昂的近卫 ×2：重型坦
    for _ in range(2):
        deck.append(Card("巴格拉季昂的近卫", 6, 5, 6, UnitType.GUARD, Faction.RUSSIA,
                         Line.MAIN, ["结阵", "守卫"]))

    # 库图佐夫的旗手 ×1：自残 2，全场 +1 攻
    deck.append(Card("库图佐夫的旗手", 6, 4, 6, UnitType.GUARD, Faction.RUSSIA,
                     Line.MAIN, ["结阵", "守卫", "自残2", "光环+1攻"]))

    # 帝国大军 ×1：自残 1，全场 +1 血
    deck.append(Card("帝国大军", 5, 3, 5, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.MAIN, ["结阵", "自残1", "光环+1血"]))

    # === v0.3B 新卡 ===
    # 顿河哥萨克猎骑：Cossack swarm economy
    deck.append(Card("顿河哥萨克猎骑", 3, 3, 3, UnitType.CAVALRY, Faction.RUSSIA,
                     Line.MAIN, ["冲锋", "侧翼迂回", "熔岩战术", "On Destroy"],
                     subfaction=SubFaction.COSSACK))

    # 撤退中的炮兵队：On Advance cameo (Russia surprise)
    deck.append(Card("撤退中的炮兵队", 4, 3, 3, UnitType.ARTILLERY, Faction.RUSSIA,
                     Line.REAR, ["远程", "焦土补给", "On Advance"]))

    # 焦土游击：Cheap Cossack meat with On Destroy
    deck.append(Card("焦土游击", 2, 2, 2, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.MAIN, ["自残1", "焦土补给", "On Destroy"],
                     subfaction=SubFaction.COSSACK))

    # 库图佐夫的传令兵：EVENT with On Deploy (death → extend)
    deck.append(Card("库图佐夫的传令兵", 1, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, ["On Deploy"],
                     CardType.EVENT, "buff_cossack_death_extend"))

    # === 事件卡 ===
    deck.append(Card("库图佐夫的战略后撤", 1, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "retreat_friendly_heal2_hq1"))
    deck.append(Card("焦土政策", 2, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "self_hq1_damage_enemy_skirmish1"))
    deck.append(Card("冬将军", 3, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "weather_winter_all_damage1"))

    # === 扩展事件 / 将领卡 ===
    deck.append(Card("巴格拉季昂后卫军", 2, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "fortify_target_INF_GUARD+0+2_guard"))
    deck.append(Card("库图佐夫的撤退令", 2, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "retreat_friendly_heal2_hq1"))
    deck.append(Card("焦土伏击", 1, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "self_hq1_damage_enemy_skirmish1"))

    return deck


# 阵营 → 牌库 构建函数的映射
DECK_BUILDERS = {
    Faction.FRANCE: build_france_deck,
    Faction.PRUSSIA: build_prussia_deck,
    Faction.RUSSIA: build_russia_deck,
}
