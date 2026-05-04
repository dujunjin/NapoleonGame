import unittest

from cards import Card, Faction, Line, UnitType
from combat import execute_attack, find_attack_targets
from game import deploy_card, play_turn
from ai import choose_units_to_advance
from game_state import Battlefield, BattleUnit, Player


class RuleTuningTests(unittest.TestCase):
    def make_card(self, name, cost=1, attack=1, health=1, keywords=None, unit_type=UnitType.INFANTRY, deploy_line=Line.MAIN):
        return Card(
            name=name,
            cost=cost,
            attack=attack,
            health=health,
            unit_type=unit_type,
            faction=Faction.FRANCE,
            deploy_line=deploy_line,
            keywords=keywords or [],
        )

    def test_turn_draws_two_cards_when_hand_is_low(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            deck=[self.make_card("补给1", cost=99), self.make_card("补给2", cost=99)],
            hand=[self.make_card("手牌", cost=99)],
            hq_hp=25,
            max_orders=2,
            current_orders=2,
        )
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)
        log = []

        play_turn(player, opponent, Battlefield(), 0, 1, log)

        self.assertTrue(any("抽到 补给1、补给2" in entry for entry in log))
        self.assertEqual(len(player.hand), 3)

    def test_orders_growth_slows_after_six_orders(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            deck=[],
            hand=[],
            hq_hp=25,
            max_orders=6,
            current_orders=6,
        )
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)
        log = []

        play_turn(player, opponent, Battlefield(), 0, 5, log)

        self.assertEqual(player.max_orders, 6)
        self.assertTrue(any("军令: 6/6" in entry for entry in log))

    def test_orders_increase_every_other_turn_after_six_orders(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            deck=[],
            hand=[],
            hq_hp=25,
            max_orders=6,
            current_orders=6,
        )
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)

        play_turn(player, opponent, Battlefield(), 0, 6, [])

        self.assertEqual(player.max_orders, 7)

    def test_death_log_names_the_dead_unit(self):
        attacker = BattleUnit(
            card=self.make_card("攻击者", attack=3, health=3),
            current_hp=3,
            current_line=Line.MAIN,
            deployed_this_turn=False,
        )
        defender = BattleUnit(
            card=self.make_card("被击杀单位", attack=0, health=2),
            current_hp=2,
            current_line=Line.MAIN,
            deployed_this_turn=False,
        )
        log = []

        execute_attack(attacker, defender, log)

        self.assertIn("目标阵亡：被击杀单位", log[0])

    def test_deploy_card_uses_center_slots_before_edges(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            hand=[self.make_card("中路1"), self.make_card("中路2")],
            current_orders=10,
        )
        battlefield = Battlefield()

        deploy_card(player, player.hand[0], battlefield, 0)
        deploy_card(player, player.hand[0], battlefield, 0)

        self.assertEqual([u.slot for u in battlefield.get_line(0, Line.MAIN)], [1, 2])

    def test_advance_fails_when_matching_skirmish_slot_is_occupied(self):
        battlefield = Battlefield()
        player = Player(name="P1", faction=Faction.FRANCE, current_orders=3)
        main_unit = BattleUnit(
            card=self.make_card("待前压", cost=2),
            current_hp=3,
            current_line=Line.MAIN,
            slot=1,
            deployed_this_turn=False,
        )
        blocker = BattleUnit(
            card=self.make_card("占位散兵", unit_type=UnitType.SKIRMISHER, deploy_line=Line.SKIRMISH),
            current_hp=2,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        battlefield.p1_main.append(main_unit)
        battlefield.p1_skirmish.append(blocker)

        self.assertEqual(choose_units_to_advance(player, battlefield, 0), [])

    def test_infantry_attacks_only_adjacent_opposing_skirmish_slot(self):
        battlefield = Battlefield()
        attacker = BattleUnit(
            card=self.make_card("步兵", attack=2),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        aligned_target = BattleUnit(
            card=self.make_card("正面敌人", health=3),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        offset_target = BattleUnit(
            card=self.make_card("错位敌人", health=3),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=2,
            deployed_this_turn=False,
        )
        battlefield.p1_skirmish.append(attacker)
        battlefield.p2_skirmish.extend([aligned_target, offset_target])

        self.assertEqual(find_attack_targets(battlefield, attacker, 0), [aligned_target])

    def test_skirmisher_range_two_can_attack_adjacent_offset(self):
        battlefield = Battlefield()
        attacker = BattleUnit(
            card=self.make_card("散兵", unit_type=UnitType.SKIRMISHER, deploy_line=Line.SKIRMISH),
            current_hp=2,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        target = BattleUnit(
            card=self.make_card("斜向敌人"),
            current_hp=2,
            current_line=Line.SKIRMISH,
            slot=2,
            deployed_this_turn=False,
        )
        battlefield.p1_skirmish.append(attacker)
        battlefield.p2_skirmish.append(target)

        self.assertEqual(find_attack_targets(battlefield, attacker, 0), [target])

    def test_artillery_range_three_reaches_skirmish_but_not_enemy_main(self):
        battlefield = Battlefield()
        attacker = BattleUnit(
            card=self.make_card("火炮", unit_type=UnitType.ARTILLERY, deploy_line=Line.REAR, keywords=["远程"]),
            current_hp=3,
            current_line=Line.REAR,
            slot=1,
            deployed_this_turn=False,
        )
        skirmish_target = BattleUnit(
            card=self.make_card("散兵目标"),
            current_hp=2,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        main_target = BattleUnit(
            card=self.make_card("主力目标"),
            current_hp=3,
            current_line=Line.MAIN,
            slot=1,
            deployed_this_turn=False,
        )
        battlefield.p1_rear.append(attacker)
        battlefield.p2_skirmish.append(skirmish_target)
        battlefield.p2_main.append(main_target)

        self.assertEqual(find_attack_targets(battlefield, attacker, 0), [skirmish_target])

    def test_flanking_cavalry_effective_range_is_three(self):
        battlefield = Battlefield()
        attacker = BattleUnit(
            card=self.make_card("侧翼骑兵", unit_type=UnitType.CAVALRY, keywords=["冲锋", "侧翼迂回"]),
            current_hp=3,
            current_line=Line.MAIN,
            slot=1,
            deployed_this_turn=False,
        )
        range_two_target = BattleUnit(
            card=self.make_card("二格目标"),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        range_three_target = BattleUnit(
            card=self.make_card("三格目标"),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=2,
            deployed_this_turn=False,
        )
        battlefield.p1_main.append(attacker)
        battlefield.p2_skirmish.extend([range_two_target, range_three_target])

        self.assertEqual(find_attack_targets(battlefield, attacker, 0), [range_two_target, range_three_target])


if __name__ == "__main__":
    unittest.main()
