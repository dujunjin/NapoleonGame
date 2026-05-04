"""
拿破仑卡牌游戏规则模拟器 - 游戏状态

核心数据结构：
- BattleUnit: 场上单位实例（不是 Card，因为有 hp 损耗等运行时状态）
- Battlefield: 战场，管理三线
- Player: 玩家状态（手牌、牌库、HQ、军令）
- GameState: 完整对局状态
"""

from dataclasses import dataclass, field
from typing import List, Optional
from cards import Card, Line, Faction
import random


@dataclass
class BattleUnit:
    """场上的单位实例"""
    card: Card
    current_hp: int
    current_line: Line
    slot: int = 0
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
    max_orders: int = 0
    current_orders: int = 0

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
    """战场，管理双方三条线，每条线有 4 个横向槽位。"""
    LINE_CAPACITY = 4
    SLOT_PRIORITY = (1, 2, 0, 3)

    p1_rear: List[BattleUnit] = field(default_factory=list)
    p1_main: List[BattleUnit] = field(default_factory=list)
    p1_skirmish: List[BattleUnit] = field(default_factory=list)
    p2_skirmish: List[BattleUnit] = field(default_factory=list)
    p2_main: List[BattleUnit] = field(default_factory=list)
    p2_rear: List[BattleUnit] = field(default_factory=list)

    def get_line(self, player_idx: int, line: Line) -> List[BattleUnit]:
        """返回指定玩家在指定线的单位列表（可修改）"""
        if player_idx == 0:
            return {
                Line.REAR: self.p1_rear,
                Line.MAIN: self.p1_main,
                Line.SKIRMISH: self.p1_skirmish,
            }[line]
        return {
            Line.REAR: self.p2_rear,
            Line.MAIN: self.p2_main,
            Line.SKIRMISH: self.p2_skirmish,
        }[line]

    def occupied_slots(self, player_idx: int, line: Line) -> set[int]:
        """返回指定线已被占用的槽位。"""
        if line == Line.SKIRMISH:
            return {unit.slot for unit in self.p1_skirmish + self.p2_skirmish}
        return {unit.slot for unit in self.get_line(player_idx, line)}

    def is_slot_empty(self, player_idx: int, line: Line, slot: int) -> bool:
        """指定槽位是否可用。"""
        return 0 <= slot < self.LINE_CAPACITY and slot not in self.occupied_slots(player_idx, line)

    def choose_deploy_slot(self, player_idx: int, line: Line) -> Optional[int]:
        """AI 默认部署槽位：优先中路，再到边路。"""
        for slot in self.SLOT_PRIORITY:
            if self.is_slot_empty(player_idx, line, slot):
                return slot
        return None

    def can_deploy(self, player_idx: int, line: Line, slot: Optional[int] = None) -> bool:
        """该线或指定槽位是否还有空位。"""
        if slot is not None:
            return self.is_slot_empty(player_idx, line, slot)
        return self.choose_deploy_slot(player_idx, line) is not None

    def sort_line(self, player_idx: int, line: Line):
        """按横向槽位排序，保证日志、AI 和导出稳定。"""
        self.get_line(player_idx, line).sort(key=lambda unit: unit.slot)

    def row_index(self, player_idx: int, line: Line) -> int:
        """从 P1 视角返回二维战场行号。"""
        if player_idx == 0:
            return {
                Line.REAR: 0,
                Line.MAIN: 1,
                Line.SKIRMISH: 2,
            }[line]
        return {
            Line.SKIRMISH: 2,
            Line.MAIN: 3,
            Line.REAR: 4,
        }[line]

    def distance(self, attacker_player_idx: int, attacker: BattleUnit, target: BattleUnit) -> int:
        """返回攻击者到敌方目标的曼哈顿距离。"""
        target_player_idx = 1 - attacker_player_idx
        row_delta = abs(self.row_index(attacker_player_idx, attacker.current_line)
                        - self.row_index(target_player_idx, target.current_line))
        slot_delta = abs(attacker.slot - target.slot)
        return row_delta + slot_delta

    def cleanup_dead(self):
        """清理所有阵亡单位"""
        for line_list in [
            self.p1_rear,
            self.p1_main,
            self.p1_skirmish,
            self.p2_rear,
            self.p2_main,
            self.p2_skirmish,
        ]:
            line_list[:] = [u for u in line_list if not u.is_dead]

    def all_units(self, player_idx: int) -> List[BattleUnit]:
        """返回某玩家所有场上单位"""
        if player_idx == 0:
            return self.p1_rear + self.p1_main + self.p1_skirmish
        return self.p2_rear + self.p2_main + self.p2_skirmish

    def opponent_blockers(self, attacker_player_idx: int, attacker_line: Line) -> List[BattleUnit]:
        """返回攻击者可能面对的敌方单位。"""
        opp_idx = 1 - attacker_player_idx
        return self.all_units(opp_idx)
