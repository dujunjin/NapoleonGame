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
from game_state import Player, Battlefield, BattleUnit
from ai import choose_cards_to_play, ai_attack_phase, choose_units_to_advance
from cards import Line, UnitType


# ========== 配置 ==========
STARTING_HQ_HP = 14         # HQ 起始血量（解决 30% 软超时：从 16 降到 14）
STARTING_HAND_SIZE = 4      # 起手抽牌
SECOND_PLAYER_BONUS_DRAW = 1 # 后手额外起手牌
TURN_DRAW_COUNT = 2         # 每轮发牌
MAX_HAND_SIZE = 7           # 手牌上限
INITIAL_ORDERS = 1          # 起始军令
ORDERS_GROWTH_PER_TURN = 1  # 每回合军令+1
MAX_ORDERS = 16             # 军令上限
MAX_TURNS = 30              # 倒计时上限（40→30，收紧节奏）


@dataclass
class GameResult:
    winner: int               # 0 / 1，平局为 -1
    turns: int
    p1_hq_remaining: int
    p2_hq_remaining: int
    p1_units_played: int
    p2_units_played: int
    end_reason: str


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
        return _play_event_card(player, card, battlefield, player_idx, log)

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
    
    if log is not None:
        log.append(f"  ▶ {player.name} 部署 {card.name} 到 {target_line.value} 槽位{target_slot + 1}")
    
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
    
    return True


def _apply_aura(card: Card, attack_bonus: int = 0, health_bonus: int = 0) -> Card:
    """生成一个数值修改后的 Card 副本（光环效果）"""
    from dataclasses import replace
    return replace(card,
                   attack=card.attack + attack_bonus,
                   health=card.health + health_bonus)


def _play_event_card(player: Player, card: Card, battlefield: Battlefield,
                     player_idx: int, log: list = None) -> bool:
    """解析事件卡，不上场。失败（无合法目标 / 军令不足）返回 False。"""
    if player.current_orders < card.cost:
        return False

    if card.event_effect == "buff_target_INF+1+2":
        # 选择一个我方 INFANTRY 单位，永久 +1/+2 并立即回血 2
        targets = [u for u in battlefield.all_units(player_idx)
                   if u.card.unit_type == UnitType.INFANTRY]
        if not targets:
            return False  # 无合法目标，事件无法打出
        # AI 启发式：优先强化当前 HP 最低的步兵（救场）
        target = min(targets, key=lambda u: u.current_hp)
        target.card = _apply_aura(target.card, attack_bonus=1, health_bonus=2)
        target.current_hp += 2
        player.hand.remove(card)
        player.discard_pile.append(card)
        player.current_orders -= card.cost
        if log is not None:
            log.append(
                f"  📜 {player.name} 打出事件卡【{card.name}】→ 强化 "
                f"{target.card.name} (+1/+2)（现 {target.card.attack}/{target.card.health}, hp {target.current_hp}）"
            )
        return True

    return False


def play_turn(
    active: Player,
    opponent: Player,
    battlefield: Battlefield,
    active_idx: int,
    turn_num: int,
    log: list = None
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
    
    # 4. 攻击阶段
    hq_damage = ai_attack_phase(active, opponent, battlefield, active_idx, log)
    stats["hq_damage_dealt"] = hq_damage
    
    if log is not None:
        log.append(f"  状态：P1 HQ={battlefield.p1_rear and 'X' or ''}{active.hq_hp if active_idx == 0 else opponent.hq_hp}, "
                   f"P2 HQ={active.hq_hp if active_idx == 1 else opponent.hq_hp}")
    
    return stats


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

    p1_units_played = 0
    p2_units_played = 0

    if log is not None:
        log.append(f"\n{'='*60}")
        log.append(f"  ⏳ 倒计时开始：最大 {MAX_TURNS} 回合")
        log.append(f"{'='*60}")

    # 主循环：先后手交替
    for turn in range(1, MAX_TURNS + 1):
        countdown = MAX_TURNS - turn

        if log is not None:
            log.append(f"\n--- 倒计时：剩余 {countdown} 回合 ---")

        # P1 回合
        stats = play_turn(p1, p2, battlefield, 0, turn, log)
        p1_units_played += stats["units_played"]

        if p2.hq_hp <= 0:
            if verbose and log:
                print("\n".join(log))
            return GameResult(winner=0, turns=turn,
                              p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                              p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                              end_reason="P2 HQ 摧毁")

        # P2 回合
        stats = play_turn(p2, p1, battlefield, 1, turn, log)
        p2_units_played += stats["units_played"]

        if p1.hq_hp <= 0:
            if verbose and log:
                print("\n".join(log))
            return GameResult(winner=1, turns=turn,
                              p1_hq_remaining=p1.hq_hp, p2_hq_remaining=p2.hq_hp,
                              p1_units_played=p1_units_played, p2_units_played=p2_units_played,
                              end_reason="P1 HQ 摧毁")

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
                              end_reason=f"倒计时结束，HQ血量判定 (P1:{p1.hq_hp} vs P2:{p2.hq_hp})")

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
                      end_reason=f"超时 ({MAX_TURNS} 回合)")


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
