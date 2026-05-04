import unittest

from cards import Card, Faction, Line, UnitType
from combat import execute_attack
from game import play_turn
from game_state import Battlefield, BattleUnit, Player


class RuleTuningTests(unittest.TestCase):
    def make_card(self, name, cost=1, attack=1, health=1, keywords=None):
        return Card(
            name=name,
            cost=cost,
            attack=attack,
            health=health,
            unit_type=UnitType.INFANTRY,
            faction=Faction.FRANCE,
            deploy_line=Line.MAIN,
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


if __name__ == "__main__":
    unittest.main()
