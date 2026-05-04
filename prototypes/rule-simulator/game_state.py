"""
拿破仑卡牌游戏规则模拟器 - 游戏状态

核心数据结构：
- BattleUnit: 场上单位实例（不是 Card，因为有 hp 损耗等运行时状态）
- Battlefield: 战场，管理三线
- Player: 玩家状态（手牌、牌库、HQ、军令）
- GameState: 完整对局状态
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from cards import Card, Line, UnitType, Faction
import random


@dataclass
class BattleUnit:
    """场上的单位实例"""
    card: Card
    current_hp: int
    current_line: Line
    has_acted_this_turn: bool = False
    deployed_this_turn: bool = True
    has_used_evade: bool = False
    
    @property
    def is_dead(self) -> bool:
        return self.current_hp <= 0
    
    @property
    def can_act(self) -> bool:
        if self.is_dead:
            return False
        if self.has_acted_this_turn:
            return False
        # 部署当回合，没有"冲锋"关键词的不能行动
        if self.deployed_this_turn and "冲锋" not in self.card.keywords:
            return False
        return True
    
    def __repr__(self):
        return f"{self.card.name}[{self.current_hp}/{self.card.health}]"


@dataclass
class Player:
    """玩家状态"""
    name: str
    faction: Faction
    deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    hq_hp: int = 20
    max_orders: int = 0       # 当前回合上限
    current_orders: int = 0   # 当前可用
    
    def draw(self, n: int = 1) -> List[Card]:
        """抽 n 张牌，牌库空了就略过（不烧伤）"""
        drawn = []
        for _ in range(n):
            if self.deck:
                card = self.deck.pop(0)
                self.hand.append(card)
                drawn.append(card)
        return drawn
    
    def shuffle_deck(self):
        random.shuffle(self.deck)


@dataclass
class Battlefield:
    """战场，管理三条线
    
    每个玩家的部署情况：
    - REAR: 自己的后方（炮兵阵地）
    - MAIN: 自己的主力战列线
    - SKIRMISH: 公共散兵线（双方共享，但区分敌我单位）
    
    SKIRMISH 容量 4，REAR/MAIN 各容量 4。
    """
    LINE_CAPACITY = 4
    
    # 玩家1的单位
    p1_rear: List[BattleUnit] = field(default_factory=list)
    p1_main: List[BattleUnit] = field(default_factory=list)
    # 公共散兵线（按玩家分开存）
    p1_skirmish: List[BattleUnit] = field(default_factory=list)
    p2_skirmish: List[BattleUnit] = field(default_factory=list)
    # 玩家2的单位
    p2_main: List[BattleUnit] = field(default_factory=list)
    p2_rear: List[BattleUnit] = field(default_factory=list)
    
    def get_line(self, player_idx: int, line: Line) -> List[BattleUnit]:
        """返回指定玩家在指定线的单位列表（可修改）"""
        if player_idx == 0:
            return {Line.REAR: self.p1_rear, Line.MAIN: self.p1_main, 
                    Line.SKIRMISH: self.p1_skirmish}[line]
        else:
            return {Line.REAR: self.p2_rear, Line.MAIN: self.p2_main,
                    Line.SKIRMISH: self.p2_skirmish}[line]
    
    def can_deploy(self, player_idx: int, line: Line) -> bool:
        """该线是否还有空位"""
        return len(self.get_line(player_idx, line)) < self.LINE_CAPACITY
    
    def cleanup_dead(self):
        """清理所有阵亡单位"""
        for line_list in [self.p1_rear, self.p1_main, self.p1_skirmish,
                          self.p2_rear, self.p2_main, self.p2_skirmish]:
            line_list[:] = [u for u in line_list if not u.is_dead]
    
    def all_units(self, player_idx: int) -> List[BattleUnit]:
        """返回某玩家所有场上单位"""
        if player_idx == 0:
            return self.p1_rear + self.p1_main + self.p1_skirmish
        else:
            return self.p2_rear + self.p2_main + self.p2_skirmish
    
    def opponent_blockers(self, attacker_player_idx: int, attacker_line: Line) -> List[BattleUnit]:
        """攻击者从哪条线攻击时，敌方有哪些单位可以被攻击 / 必须被先攻击
        
        规则：
        - 主力线必须先解决散兵线和敌方主力线的守卫
        - 散兵线可以攻击敌方散兵线和主力线
        - 后方炮兵远程攻击：可以攻击散兵线、主力线
        - 侧翼迂回单位（在散兵线）可以无视主力直接打后方
        """
        opp_idx = 1 - attacker_player_idx
        # 先返回所有可能的目标，逻辑判断在战斗系统里
        return self.all_units(opp_idx)
