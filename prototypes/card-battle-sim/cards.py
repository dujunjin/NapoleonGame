"""
拿破仑卡牌游戏规则模拟器 - 卡牌定义

设计原则：
- 数据驱动：所有卡牌都是数据，不是写死的逻辑
- 关键词系统：通过关键词组合表达兵种特性，避免一卡一逻辑
- 简化但保留拿战核心：步兵阵型、骑兵冲锋、炮兵远程、散兵骚扰
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


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


@dataclass
class Card:
    """卡牌定义"""
    name: str
    cost: int                      # 军令消耗
    attack: int
    health: int
    unit_type: UnitType
    faction: Faction
    deploy_line: Line              # 默认部署在哪条线
    keywords: List[str] = field(default_factory=list)
    
    def __repr__(self):
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
# 
# === 俄罗斯阵营专用关键词（部署时触发，on-play 类型）===
# "自残N"    - 部署时对自己 HQ 造成 N 点伤害（代价）
# "光环+1攻" - 部署后，所有其他友军单位永久 +1 攻击力
# "光环+1血" - 部署后，所有其他友军单位永久 +1 血量上限


# ============================================================
# 法兰西阵营牌库（30 张：以 3 张为一种 × 10 种）
# 风格：高攻击力、纵队冲锋、近卫精锐
# ============================================================
def build_france_deck() -> List[Card]:
    deck = []
    
    # 散兵 ×3：低费骚扰
    for i in range(3):
        deck.append(Card("猎兵连", 1, 1, 2, UnitType.SKIRMISHER, Faction.FRANCE,
                         Line.SKIRMISH, ["闪避"]))
    
    # 线列步兵 ×4：主力
    for i in range(4):
        deck.append(Card("第45线列步兵团", 3, 3, 4, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵", "齐射"]))
    
    # 高费精锐线列 ×3：法军核心
    for i in range(3):
        deck.append(Card("近卫掷弹兵", 5, 5, 5, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵", "齐射", "守卫"]))
    
    # 龙骑兵 ×3：中费骑兵
    for i in range(3):
        deck.append(Card("龙骑兵团", 4, 4, 3, UnitType.CAVALRY, Faction.FRANCE,
                         Line.MAIN, ["冲锋"]))
    
    # 胸甲骑兵 ×2：高费重骑
    for i in range(2):
        deck.append(Card("胸甲骑兵", 6, 6, 5, UnitType.CAVALRY, Faction.FRANCE,
                         Line.MAIN, ["冲锋", "突破"]))
    
    # 骑炮 ×2：机动炮兵
    for i in range(2):
        deck.append(Card("近卫马炮兵", 4, 3, 2, UnitType.ARTILLERY, Faction.FRANCE,
                         Line.REAR, ["远程"]))
    
    # 重炮 ×2：高费后排炮
    for i in range(2):
        deck.append(Card("12磅野战炮", 5, 4, 3, UnitType.ARTILLERY, Faction.FRANCE,
                         Line.REAR, ["远程"]))
    
    # 老近卫 ×1：终极牌
    deck.append(Card("老近卫军", 8, 7, 8, UnitType.GUARD, Faction.FRANCE,
                     Line.MAIN, ["结阵", "齐射", "守卫", "突破"]))
    
    # 轻骑兵 ×3：低费骑兵
    for i in range(3):
        deck.append(Card("骠骑兵", 2, 2, 2, UnitType.CAVALRY, Faction.FRANCE,
                         Line.MAIN, ["冲锋", "侧翼迂回"]))
    
    # 步兵纵队 ×3：低费铺场步兵
    for i in range(3):
        deck.append(Card("征召步兵营", 2, 2, 3, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵"]))
    
    # 大军步兵 ×4：中费铺场
    for i in range(4):
        deck.append(Card("帝国步兵团", 4, 4, 4, UnitType.INFANTRY, Faction.FRANCE,
                         Line.MAIN, ["结阵", "齐射"]))
    
    return deck


# ============================================================
# 普鲁士阵营牌库（30 张）
# 风格：散兵改革、低费过牌、机动突袭
# ============================================================
def build_prussia_deck() -> List[Card]:
    deck = []
    
    # 散兵 ×4：普鲁士军事改革核心
    for i in range(4):
        deck.append(Card("耶格猎兵", 1, 2, 2, UnitType.SKIRMISHER, Faction.PRUSSIA,
                         Line.SKIRMISH, ["闪避", "齐射"]))
    
    # 国民军 ×4：低费铺场步兵
    for i in range(4):
        deck.append(Card("西里西亚国民军", 2, 2, 3, UnitType.INFANTRY, Faction.PRUSSIA,
                         Line.MAIN, ["结阵"]))
    
    # 线列步兵 ×4：主力
    for i in range(4):
        deck.append(Card("普鲁士线列军", 3, 3, 4, UnitType.INFANTRY, Faction.PRUSSIA,
                         Line.MAIN, ["结阵", "齐射"]))
    
    # 掷弹兵 ×3：精锐步兵
    for i in range(3):
        deck.append(Card("近卫掷弹兵团", 4, 4, 5, UnitType.INFANTRY, Faction.PRUSSIA,
                         Line.MAIN, ["结阵", "齐射", "守卫"]))
    
    # 黑色骠骑兵 ×3：低费骑兵
    for i in range(3):
        deck.append(Card("死骑兵", 2, 2, 2, UnitType.CAVALRY, Faction.PRUSSIA,
                         Line.MAIN, ["冲锋", "侧翼迂回"]))
    
    # 龙骑兵 ×2
    for i in range(2):
        deck.append(Card("普鲁士龙骑", 4, 4, 3, UnitType.CAVALRY, Faction.PRUSSIA,
                         Line.MAIN, ["冲锋"]))
    
    # 步兵炮 ×3
    for i in range(3):
        deck.append(Card("步兵炮组", 3, 2, 3, UnitType.ARTILLERY, Faction.PRUSSIA,
                         Line.REAR, ["远程"]))
    
    # 重炮 ×2
    for i in range(2):
        deck.append(Card("普鲁士重炮", 5, 5, 3, UnitType.ARTILLERY, Faction.PRUSSIA,
                         Line.REAR, ["远程"]))
    
    # 黑色布伦瑞克军 ×2：精锐
    for i in range(2):
        deck.append(Card("黑色布伦瑞克", 5, 5, 4, UnitType.INFANTRY, Faction.PRUSSIA,
                         Line.MAIN, ["结阵", "突破"]))
    
    # 元帅近卫 ×3：高数值
    for i in range(3):
        deck.append(Card("布吕歇尔的近卫", 6, 6, 6, UnitType.GUARD, Faction.PRUSSIA,
                         Line.MAIN, ["结阵", "守卫"]))
    
    return deck


# ============================================================
# 俄罗斯阵营牌库（30 张）
# 风格：低费铺场 + HQ 自残换效果 + 哥萨克侧翼骚扰
# 核心定位：消耗战、肉盾耐打、靠后期光环和侧翼威胁取胜
# ============================================================
def build_russia_deck() -> List[Card]:
    deck = []
    
    # 哥萨克轻骑 ×2：低费骚扰骑兵（从 4 张减到 2 张）
    for i in range(2):
        deck.append(Card("哥萨克轻骑", 1, 2, 1, UnitType.CAVALRY, Faction.RUSSIA,
                         Line.MAIN, ["冲锋", "侧翼迂回"]))
    
    # 俄军猎兵团 ×2：占据散兵线的低费散兵（新增，解决散兵线劣势）
    for i in range(2):
        deck.append(Card("俄军猎兵团", 1, 1, 2, UnitType.SKIRMISHER, Faction.RUSSIA,
                         Line.SKIRMISH, ["闪避"]))
    
    # 东正教民兵 ×4：超低费铺场步兵
    for i in range(4):
        deck.append(Card("东正教民兵", 2, 2, 3, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵"]))
    
    # 俄国线列军 ×4：高血量肉盾，攻击力低（消耗战定位）
    for i in range(4):
        deck.append(Card("俄国线列军", 3, 2, 5, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵"]))
    
    # 步兵炮 ×2：基础炮兵
    for i in range(2):
        deck.append(Card("俄军步兵炮", 3, 3, 2, UnitType.ARTILLERY, Faction.RUSSIA,
                         Line.REAR, ["远程"]))
    
    # 西伯利亚老兵 ×3：自残 1 点 HQ，换得超模数值（数值升级 5/4 → 6/5）
    for i in range(3):
        deck.append(Card("西伯利亚老兵", 3, 5, 5, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵", "自残1"]))
    
    # 普拉托夫的哥萨克 ×3：高数值侧翼骑兵
    for i in range(3):
        deck.append(Card("普拉托夫的哥萨克", 4, 3, 2, UnitType.CAVALRY, Faction.RUSSIA,
                         Line.MAIN, ["冲锋", "侧翼迂回"]))
    
    # 龙骑兵 ×2：标准骑兵
    for i in range(2):
        deck.append(Card("俄军龙骑", 4, 4, 3, UnitType.CAVALRY, Faction.RUSSIA,
                         Line.MAIN, ["冲锋"]))
    
    # 莫斯科掷弹兵 ×2：中费精锐
    for i in range(2):
        deck.append(Card("莫斯科掷弹兵", 5, 4, 5, UnitType.INFANTRY, Faction.RUSSIA,
                         Line.MAIN, ["结阵", "守卫"]))
    
    # 独角兽榴弹炮 ×2：重型炮
    for i in range(2):
        deck.append(Card("独角兽榴弹炮", 5, 5, 3, UnitType.ARTILLERY, Faction.RUSSIA,
                         Line.REAR, ["远程"]))
    
    # 巴格拉季昂的近卫 ×2：重型坦
    for i in range(2):
        deck.append(Card("巴格拉季昂的近卫", 6, 5, 6, UnitType.GUARD, Faction.RUSSIA,
                         Line.MAIN, ["结阵", "守卫"]))
    
    # 库图佐夫的旗手 ×1：自残 2 点 HQ，换全场 +1 攻击力光环
    deck.append(Card("库图佐夫的旗手", 6, 4, 6, UnitType.GUARD, Faction.RUSSIA,
                     Line.MAIN, ["结阵", "守卫", "自残2", "光环+1攻"]))
    
    # 帝国大军 ×1：自残 1，光环 +1 血
    deck.append(Card("帝国大军", 5, 3, 5, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.MAIN, ["结阵", "自残1", "光环+1血"]))
    
    return deck


# 阵营 → 牌库 构建函数的映射
DECK_BUILDERS = {
    Faction.FRANCE: build_france_deck,
    Faction.PRUSSIA: build_prussia_deck,
    Faction.RUSSIA: build_russia_deck,
}
