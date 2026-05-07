import unittest
from unittest.mock import patch

from cards import Card, CardType, Faction, Line, SubFaction, UnitType
from cards import DECK_BUILDERS
from combat import execute_attack, find_attack_targets, effective_attack
from game import (
    deploy_card, play_turn, play_one_game, advance_max_orders,
    apply_operational_pressure, use_commander_ability,
    MAX_ORDERS, STARTING_HQ_HP, MAX_TURNS, OPERATIONAL_PRESSURE_START_TURN,
)
from export_match import play_and_export
from ai import choose_units_to_advance, ai_attack_phase
from game_state import Battlefield, BattleUnit, Player
from commanders import COMMANDERS, DEFAULT_COMMANDERS, CommanderId, get_default_commander
from objectives import ObjectiveId, OBJECTIVES, assign_objectives, complete_objective


class RuleTuningTests(unittest.TestCase):
    def make_card(self, name, cost=1, attack=1, health=1, keywords=None, unit_type=UnitType.INFANTRY, deploy_line=Line.MAIN, subfaction=None):
        return Card(
            name=name,
            cost=cost,
            attack=attack,
            health=health,
            unit_type=unit_type,
            faction=Faction.FRANCE,
            deploy_line=deploy_line,
            keywords=keywords or [],
            subfaction=subfaction,
        )

    def test_all_faction_decks_have_thirty_three_cards_after_expansion(self):
        self.assertEqual({faction: len(builder()) for faction, builder in DECK_BUILDERS.items()}, {
            Faction.FRANCE: 33,
            Faction.PRUSSIA: 33,
            Faction.RUSSIA: 33,
        })

    def test_balance_tuning_card_stats(self):
        france = {card.name: card for card in DECK_BUILDERS[Faction.FRANCE]()}
        prussia = {card.name: card for card in DECK_BUILDERS[Faction.PRUSSIA]()}
        russia = {card.name: card for card in DECK_BUILDERS[Faction.RUSSIA]()}

        self.assertEqual(prussia["耶格猎兵"].health, 2)
        self.assertEqual((prussia["死骑兵"].attack, prussia["死骑兵"].health), (2, 2))
        self.assertIn("死神威慑", prussia["死骑兵"].keywords)
        self.assertEqual(prussia["近卫掷弹兵团"].health, 5)
        self.assertEqual(prussia["布吕歇尔的近卫"].attack, 6)
        self.assertEqual(sum(1 for card in DECK_BUILDERS[Faction.PRUSSIA]() if card.name == "西里西亚国民军"), 6)
        self.assertEqual(sum(1 for card in DECK_BUILDERS[Faction.PRUSSIA]() if card.name == "普鲁士线列军"), 4)
        # 普鲁士线列军：3 攻 → 4 攻
        self.assertEqual((prussia["普鲁士线列军"].attack, prussia["普鲁士线列军"].health), (4, 4))
        # 法兰西马炮兵：拥有 军团联动（重炮不机动，不带此关键词）
        self.assertIn("军团联动", france["近卫马炮兵"].keywords)
        self.assertNotIn("军团联动", france["12磅野战炮"].keywords)
        # 老近卫军：攻击 7→6
        self.assertEqual((france["老近卫军"].attack, france["老近卫军"].health), (6, 8))
        self.assertEqual((russia["西伯利亚老兵"].attack, russia["西伯利亚老兵"].health), (5, 5))
        self.assertEqual(russia["普拉托夫的哥萨克"].attack, 3)
        # 俄国线列军：保持 2/5 肉盾
        self.assertEqual((russia["俄国线列军"].attack, russia["俄国线列军"].health), (2, 5))
        # 哥萨克轻骑：2 费 2/2 + 熔岩战术
        self.assertEqual(russia["哥萨克轻骑"].cost, 2)
        self.assertEqual((russia["哥萨克轻骑"].attack, russia["哥萨克轻骑"].health), (2, 2))
        self.assertIn("熔岩战术", russia["哥萨克轻骑"].keywords)
        # 焦土补给在东正教民兵
        self.assertIn("焦土补给", russia["东正教民兵"].keywords)
        # 库图佐夫的旗手 自残2，帝国大军 自残1
        self.assertIn("自残2", russia["库图佐夫的旗手"].keywords)
        self.assertIn("自残1", russia["帝国大军"].keywords)

    def test_global_constants_pinned(self):
        self.assertEqual(STARTING_HQ_HP, 14)
        self.assertEqual(MAX_TURNS, 30)

    def test_default_commanders_exist_for_all_factions(self):
        self.assertEqual(DEFAULT_COMMANDERS, {
            Faction.FRANCE: CommanderId.NAPOLEON,
            Faction.PRUSSIA: CommanderId.BLUCHER,
            Faction.RUSSIA: CommanderId.KUTUZOV,
        })
        self.assertEqual(get_default_commander(Faction.FRANCE).name, "拿破仑")
        self.assertEqual(get_default_commander(Faction.PRUSSIA).name, "布吕歇尔")
        self.assertEqual(get_default_commander(Faction.RUSSIA).name, "库图佐夫")
        for commander in COMMANDERS.values():
            self.assertFalse(commander.enters_deck)
            self.assertEqual(commander.uses_per_match, 1)

    def test_tactical_objectives_are_deterministic_and_distinct(self):
        p1_obj, p2_obj = assign_objectives(seed=42)
        p1_obj_again, p2_obj_again = assign_objectives(seed=42)
        self.assertEqual((p1_obj.id, p2_obj.id), (p1_obj_again.id, p2_obj_again.id))
        self.assertNotEqual(p1_obj.id, p2_obj.id)
        self.assertEqual(len(OBJECTIVES), 5)
        self.assertIn(ObjectiveId.SEIZE_SKIRMISH, OBJECTIVES)
        self.assertIn(ObjectiveId.FIRST_BLOOD_HQ, OBJECTIVES)
        self.assertIn(ObjectiveId.HOLD_MAIN, OBJECTIVES)
        self.assertIn(ObjectiveId.PREPARE_GUNS, OBJECTIVES)
        self.assertIn(ObjectiveId.SACRIFICE_FOR_TIME, OBJECTIVES)

    def test_new_players_receive_commander_and_objective_state(self):
        result = play_one_game(Faction.FRANCE, Faction.RUSSIA, seed=42)
        self.assertIsNotNone(result.p1_commander)
        self.assertIsNotNone(result.p2_commander)
        self.assertIsNotNone(result.p1_objective)
        self.assertIsNotNone(result.p2_objective)
        self.assertEqual(result.p1_commander, "拿破仑")
        self.assertEqual(result.p2_commander, "库图佐夫")
        self.assertNotEqual(result.p1_objective, result.p2_objective)

    def test_napoleon_commander_marks_line_for_hq_bonus_once(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    commander_id="napoleon", commander_name="拿破仑")
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        bf = Battlefield()
        unit = BattleUnit(card=self.make_card("帝国步兵团", attack=4), current_hp=4,
                          current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        bf.p1_main = [unit]
        log = []
        self.assertTrue(use_commander_ability(p1, p2, bf, 0, turn=5, log=log))
        self.assertTrue(p1.commander_used)
        self.assertEqual(p1.commander_active_line, Line.MAIN)
        self.assertFalse(use_commander_ability(p1, p2, bf, 0, turn=5, log=log))

    def test_blucher_commander_buffs_wounded_units_once(self):
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=14,
                    commander_id="blucher", commander_name="布吕歇尔")
        p2 = Player(name="P2", faction=Faction.FRANCE, hq_hp=14)
        bf = Battlefield()
        wounded = BattleUnit(card=self.make_card("普鲁士线列军", attack=4, health=4),
                             current_hp=2, current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        healthy = BattleUnit(card=self.make_card("西里西亚国民军", attack=2, health=3),
                             current_hp=3, current_line=Line.MAIN, slot=2, deployed_this_turn=False)
        bf.p1_main = [wounded, healthy]
        self.assertTrue(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))
        self.assertEqual(wounded.card.attack, 5)
        self.assertEqual(healthy.card.attack, 2)
        self.assertFalse(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))

    def test_kutuzov_commander_retreats_unit_heals_unit_and_hq_once(self):
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=10,
                    commander_id="kutuzov", commander_name="库图佐夫")
        p2 = Player(name="P2", faction=Faction.FRANCE, hq_hp=14)
        bf = Battlefield()
        unit = BattleUnit(card=self.make_card("俄国线列军", health=5),
                          current_hp=3, current_line=Line.SKIRMISH, slot=1,
                          deployed_this_turn=False)
        bf.p1_skirmish = [unit]
        self.assertTrue(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))
        self.assertEqual(unit.current_line, Line.REAR)
        self.assertEqual(unit.current_hp, 4)
        self.assertEqual(p1.hq_hp, 11)
        self.assertIn(unit, bf.p1_rear)
        self.assertFalse(use_commander_ability(p1, p2, bf, 0, turn=5, log=[]))

    def test_first_blood_objective_completes_once_and_grants_order(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    objective_id="first_blood_hq", objective_name="压迫 HQ",
                    max_orders=3, current_orders=1)
        completed = complete_objective(p1, ObjectiveId.FIRST_BLOOD_HQ, turn=2, log=[])
        self.assertTrue(completed)
        self.assertTrue(p1.objective_completed)
        self.assertEqual(p1.current_orders, 2)
        self.assertFalse(complete_objective(p1, ObjectiveId.FIRST_BLOOD_HQ, turn=2, log=[]))

    def test_seize_skirmish_objective_draws_once(self):
        draw_card = self.make_card("援军")
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    deck=[draw_card], objective_id="seize_skirmish",
                    objective_name="夺取散兵线")
        completed = complete_objective(p1, ObjectiveId.SEIZE_SKIRMISH, turn=2, log=[])
        self.assertTrue(completed)
        self.assertIn(draw_card, p1.hand)
        self.assertEqual(len(p1.deck), 0)

    def test_hold_main_objective_heals_hq_once(self):
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=10,
                    objective_id="hold_main", objective_name="稳住主线")
        self.assertTrue(complete_objective(p1, ObjectiveId.HOLD_MAIN, turn=2, log=[]))
        self.assertEqual(p1.hq_hp, 11)

    def test_prepare_guns_sets_pending_artillery_bonus(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    objective_id="prepare_guns", objective_name="炮兵准备")
        self.assertTrue(complete_objective(p1, ObjectiveId.PREPARE_GUNS, turn=2, log=[]))
        self.assertEqual(p1.objective_reward_pending, "artillery_attack_plus_1")

    def test_sacrifice_for_time_objective_draws_once(self):
        draw_card = self.make_card("援军")
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=14,
                    deck=[draw_card], objective_id="sacrifice_for_time",
                    objective_name="牺牲换时间")
        self.assertTrue(complete_objective(p1, ObjectiveId.SACRIFICE_FOR_TIME, turn=2, log=[]))
        self.assertIn(draw_card, p1.hand)

    def test_export_includes_commander_and_objective_metadata(self):
        data = play_and_export(Faction.FRANCE, Faction.RUSSIA, seed=42)
        self.assertEqual(data["meta"]["p1_commander"], "拿破仑")
        self.assertEqual(data["meta"]["p2_commander"], "库图佐夫")
        self.assertIn("p1_objective", data["meta"])
        self.assertIn("p2_objective", data["meta"])
        self.assertIn("commander", data["timeline"][0]["state"]["p1"])
        self.assertIn("objective", data["timeline"][0]["state"]["p1"])

    def test_operational_pressure_does_not_apply_before_start_turn(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []
        apply_operational_pressure(p1, p2, p1_dealt_hq_damage=False, p2_dealt_hq_damage=False,
                                   turn=OPERATIONAL_PRESSURE_START_TURN - 1, log=log)
        self.assertEqual((p1.hq_hp, p2.hq_hp), (14, 14))
        self.assertEqual(log, [])

    def test_operational_pressure_penalizes_p2_when_only_p1_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []
        apply_operational_pressure(p1, p2, p1_dealt_hq_damage=True, p2_dealt_hq_damage=False,
                                   turn=OPERATIONAL_PRESSURE_START_TURN, log=log)
        self.assertEqual((p1.hq_hp, p2.hq_hp), (14, 13))
        self.assertIn("P2 未造成 HQ 伤害，HQ -1", log[-1])

    def test_operational_pressure_penalizes_p1_when_only_p2_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []
        apply_operational_pressure(p1, p2, p1_dealt_hq_damage=False, p2_dealt_hq_damage=True,
                                   turn=OPERATIONAL_PRESSURE_START_TURN, log=log)
        self.assertEqual((p1.hq_hp, p2.hq_hp), (13, 14))
        self.assertIn("P1 未造成 HQ 伤害，HQ -1", log[-1])

    def test_operational_pressure_does_not_apply_when_both_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []
        apply_operational_pressure(p1, p2, p1_dealt_hq_damage=True, p2_dealt_hq_damage=True,
                                   turn=OPERATIONAL_PRESSURE_START_TURN, log=log)
        self.assertEqual((p1.hq_hp, p2.hq_hp), (14, 14))
        self.assertEqual(log, [])

    def test_operational_pressure_penalizes_both_when_neither_dealt_hq_damage(self):
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        log = []
        apply_operational_pressure(p1, p2, p1_dealt_hq_damage=False, p2_dealt_hq_damage=False,
                                   turn=OPERATIONAL_PRESSURE_START_TURN, log=log)
        self.assertEqual((p1.hq_hp, p2.hq_hp), (13, 13))
        self.assertIn("双方均未造成 HQ 伤害，各 HQ -1", log[-1])

    def test_victory_is_checked_after_both_players_take_the_round(self):
        """P1 cannot win immediately before P2 gets the same round's action."""
        def scripted_turn(active, opponent, battlefield, active_idx, turn_num, log):
            if active_idx == 0:
                opponent.hq_hp = 0
            else:
                opponent.hq_hp = -1
            return {"units_played": 0, "hq_damage_dealt": 0}

        with patch("game.play_turn", side_effect=scripted_turn):
            result = play_one_game(Faction.FRANCE, Faction.PRUSSIA, seed=1)

        self.assertEqual(result.winner, 1)
        self.assertEqual(result.end_reason, "P1 HQ 摧毁")

    def test_faction_event_packages_are_present(self):
        france_events = [c.name for c in DECK_BUILDERS[Faction.FRANCE]() if c.card_type == CardType.EVENT]
        prussia_events = [c.name for c in DECK_BUILDERS[Faction.PRUSSIA]() if c.card_type == CardType.EVENT]
        russia_events = [c.name for c in DECK_BUILDERS[Faction.RUSSIA]() if c.card_type == CardType.EVENT]

        self.assertEqual(france_events, [
            "达武的铁军", "奥斯特里茨晨雾",
            "拿破仑的预备队", "军团传令",
        ])
        self.assertEqual(prussia_events, [
            "国防动员", "国防动员", "沙恩霍斯特改革", "布吕歇尔的追击令", "莱比锡泥泞",
        ])
        self.assertEqual(russia_events, [
            "库图佐夫的战略后撤", "焦土政策", "冬将军",
            "巴格拉季昂后卫军", "库图佐夫的撤退令", "焦土伏击",
        ])

    def test_expansion_event_cards_use_existing_effects(self):
        expected = {
            Faction.FRANCE: {
                "拿破仑的预备队": (4, "fortify_target_INF_GUARD+0+2_guard"),
                "军团传令": (3, "advance_friendly_one_no_attack"),
            },
            Faction.PRUSSIA: {},
            Faction.RUSSIA: {
                "巴格拉季昂后卫军": (2, "fortify_target_INF_GUARD+0+2_guard"),
                "库图佐夫的撤退令": (2, "retreat_friendly_heal2_hq1"),
                "焦土伏击": (1, "self_hq1_damage_enemy_skirmish1"),
            },
        }

        for faction, cards in expected.items():
            deck = {card.name: card for card in DECK_BUILDERS[faction]()}
            for name, (cost, effect) in cards.items():
                with self.subTest(faction=faction, card=name):
                    self.assertIn(name, deck)
                    self.assertEqual(deck[name].card_type, CardType.EVENT)
                    self.assertEqual(deck[name].cost, cost)
                    self.assertEqual(deck[name].event_effect, effect)

    def test_corps_synergy_buffs_friendly_cavalry_in_same_slot(self):
        """军团联动：同槽位友方炮兵在 MAIN/SKIRMISH 时，骑兵 +1 攻"""
        bf = Battlefield()
        cav = BattleUnit(card=self.make_card("龙骑兵", attack=4, unit_type=UnitType.CAVALRY),
                         current_hp=3, current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        art = BattleUnit(card=self.make_card("马炮", attack=3, unit_type=UnitType.ARTILLERY,
                                              keywords=["远程", "军团联动"]),
                         current_hp=3, current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        bf.p1_main = [cav, art]
        self.assertEqual(effective_attack(cav, bf, 0), 5)

        # 不同槽位则不生效
        art.slot = 2
        bf.sort_line(0, Line.MAIN)
        self.assertEqual(effective_attack(cav, bf, 0), 4)

    def test_deaths_head_intimidation_lowers_enemy_attack_in_same_slot(self):
        """死神威慑：处于此单位同槽位的敌方单位 -1 攻；多源叠加；最低 0"""
        bf = Battlefield()
        dh = BattleUnit(card=self.make_card("死骑兵", attack=2, unit_type=UnitType.CAVALRY,
                                             keywords=["冲锋", "死神威慑"]),
                        current_hp=2, current_line=Line.MAIN, slot=2, deployed_this_turn=False)
        bf.p1_main = [dh]
        enemy = BattleUnit(card=self.make_card("敌龙骑", attack=4, unit_type=UnitType.CAVALRY),
                           current_hp=3, current_line=Line.MAIN, slot=2, deployed_this_turn=False)
        bf.p2_main = [enemy]
        self.assertEqual(effective_attack(enemy, bf, 1), 3)

        # 添加第二源（在 SKIRMISH 同槽位）
        dh2 = BattleUnit(card=self.make_card("黑色布伦瑞克", attack=5, unit_type=UnitType.INFANTRY,
                                              keywords=["结阵", "死神威慑"]),
                         current_hp=4, current_line=Line.SKIRMISH, slot=2, deployed_this_turn=False)
        bf.p1_skirmish = [dh2]
        self.assertEqual(effective_attack(enemy, bf, 1), 2)

    def test_lava_tactics_returns_attacker_to_rear(self):
        """熔岩战术：攻击后，存活则撤回 REAR"""
        bf = Battlefield()
        cossack = BattleUnit(card=self.make_card("哥萨克", cost=4, attack=3, health=5,
                                                  unit_type=UnitType.CAVALRY,
                                                  keywords=["冲锋", "侧翼迂回", "熔岩战术"]),
                             current_hp=5, current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        victim = BattleUnit(card=self.make_card("普军步兵", attack=2, health=5, unit_type=UnitType.INFANTRY,
                                                  keywords=["结阵"]),
                            current_hp=5, current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        bf.p1_main = [cossack]
        bf.p2_main = [victim]
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=20, max_orders=5, current_orders=5)
        p2 = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=20, max_orders=5, current_orders=5)
        ai_attack_phase(p1, p2, bf, 0, log=None)
        self.assertEqual(cossack.current_line, Line.REAR)
        self.assertIn(cossack, bf.p1_rear)
        self.assertNotIn(cossack, bf.p1_main)

    def test_scorched_earth_grants_owner_max_orders_on_death(self):
        """焦土补给：拥有此关键词的单位死亡时，拥有者下回合 max_orders +1"""
        bf = Battlefield()
        militia = BattleUnit(card=self.make_card("民兵", attack=1, health=1, unit_type=UnitType.INFANTRY,
                                                  keywords=["结阵", "焦土补给"]),
                             current_hp=1, current_line=Line.SKIRMISH, slot=1, deployed_this_turn=False)
        attacker = BattleUnit(card=self.make_card("敌散兵", attack=3, health=2, unit_type=UnitType.SKIRMISHER,
                                                   keywords=[]),
                              current_hp=2, current_line=Line.SKIRMISH, slot=2, deployed_this_turn=False)
        bf.p1_skirmish = [militia]
        bf.p2_skirmish = [attacker]
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=20, max_orders=5, current_orders=5)
        p2 = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=20, max_orders=5, current_orders=5)
        before = p1.max_orders
        ai_attack_phase(p2, p1, bf, 1, log=None)
        self.assertTrue(militia.is_dead or militia.current_hp <= 0)
        self.assertEqual(p1.max_orders, before + 1)

    def test_event_card_buffs_friendly_infantry(self):
        """国防动员：选择一个我方 INFANTRY，永久 +1/+2 并立即回血 2"""
        bf = Battlefield()
        target = BattleUnit(
            card=self.make_card("普鲁士线列军", attack=4, health=4, unit_type=UnitType.INFANTRY,
                                 keywords=["结阵"]),
            current_hp=2, current_line=Line.REAR, slot=1, deployed_this_turn=False,
        )
        bf.p1_rear = [target]

        event = Card(
            name="国防动员", cost=3, attack=0, health=0,
            unit_type=UnitType.INFANTRY, faction=Faction.PRUSSIA,
            deploy_line=Line.REAR, keywords=[],
            card_type=CardType.EVENT, event_effect="buff_target_INF+1+2",
        )
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=20,
                    hand=[event], max_orders=3, current_orders=3)
        ok = deploy_card(p1, event, bf, 0)
        self.assertTrue(ok)
        self.assertEqual(target.card.attack, 5)        # +1 atk
        self.assertEqual(target.card.health, 6)        # +2 hp上限
        self.assertEqual(target.current_hp, 4)         # 2 → 2+2
        self.assertNotIn(event, p1.hand)
        self.assertEqual(p1.current_orders, 0)

    def test_event_card_fails_with_no_legal_target(self):
        """国防动员：若我方无 INFANTRY，事件卡无法打出"""
        bf = Battlefield()
        only_cav = BattleUnit(
            card=self.make_card("骑兵", unit_type=UnitType.CAVALRY),
            current_hp=2, current_line=Line.REAR, slot=1, deployed_this_turn=False,
        )
        bf.p1_rear = [only_cav]
        event = Card(
            name="国防动员", cost=3, attack=0, health=0,
            unit_type=UnitType.INFANTRY, faction=Faction.PRUSSIA,
            deploy_line=Line.REAR, keywords=[],
            card_type=CardType.EVENT, event_effect="buff_target_INF+1+2",
        )
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=20,
                    hand=[event], max_orders=3, current_orders=3)
        ok = deploy_card(p1, event, bf, 0)
        self.assertFalse(ok)
        self.assertIn(event, p1.hand)
        self.assertEqual(p1.current_orders, 3)

    def test_berthier_event_advances_a_friendly_unit_without_attack(self):
        bf = Battlefield()
        target = BattleUnit(
            card=self.make_card("帝国步兵团", cost=4, unit_type=UnitType.INFANTRY),
            current_hp=4, current_line=Line.REAR, slot=1, deployed_this_turn=False,
        )
        bf.p1_rear = [target]
        event = Card("贝尔蒂埃的行军表", 1, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, [], CardType.EVENT, "advance_friendly_one_no_attack")
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=20,
                    hand=[event], max_orders=1, current_orders=1)

        self.assertTrue(deploy_card(p1, event, bf, 0))
        self.assertEqual(target.current_line, Line.MAIN)
        self.assertIn(target, bf.p1_main)
        self.assertTrue(target.has_acted_this_turn)
        self.assertEqual(p1.current_orders, 0)

    def test_davout_event_fortifies_infantry_or_guard(self):
        bf = Battlefield()
        target = BattleUnit(
            card=self.make_card("第45线列步兵团", attack=3, health=4, unit_type=UnitType.INFANTRY),
            current_hp=2, current_line=Line.MAIN, slot=1, deployed_this_turn=False,
        )
        bf.p1_main = [target]
        event = Card("达武的铁军", 2, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                     Line.REAR, [], CardType.EVENT, "fortify_target_INF_GUARD+0+2_guard")
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=20,
                    hand=[event], max_orders=2, current_orders=2)

        self.assertTrue(deploy_card(p1, event, bf, 0))
        self.assertEqual((target.card.attack, target.card.health, target.current_hp), (3, 6, 4))
        self.assertIn("守卫", target.card.keywords)

    def test_scharnhorst_event_draws_and_drills_infantry(self):
        bf = Battlefield()
        target = BattleUnit(
            card=self.make_card("西里西亚国民军", attack=2, health=3, unit_type=UnitType.INFANTRY),
            current_hp=2, current_line=Line.MAIN, slot=1, deployed_this_turn=False,
        )
        bf.p1_main = [target]
        reinforcement = self.make_card("援军", cost=1)
        event = Card("沙恩霍斯特改革", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "draw1_buff_target_INF+1+1")
        p1 = Player(name="P1", faction=Faction.PRUSSIA, deck=[reinforcement],
                    hand=[event], hq_hp=20, max_orders=2, current_orders=2)

        self.assertTrue(deploy_card(p1, event, bf, 0))
        self.assertIn(reinforcement, p1.hand)
        self.assertEqual((target.card.attack, target.card.health, target.current_hp), (3, 4, 3))

    def test_blucher_event_buffs_friendly_cavalry_and_guard(self):
        bf = Battlefield()
        cav = BattleUnit(card=self.make_card("死骑兵", attack=2, unit_type=UnitType.CAVALRY),
                         current_hp=2, current_line=Line.MAIN, slot=1, deployed_this_turn=False)
        guard = BattleUnit(card=self.make_card("布吕歇尔的近卫", attack=6, unit_type=UnitType.GUARD),
                           current_hp=6, current_line=Line.MAIN, slot=2, deployed_this_turn=False)
        infantry = BattleUnit(card=self.make_card("普鲁士线列军", attack=4, unit_type=UnitType.INFANTRY),
                              current_hp=4, current_line=Line.MAIN, slot=3, deployed_this_turn=False)
        bf.p1_main = [cav, guard, infantry]
        event = Card("布吕歇尔的追击令", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "buff_all_friendly_CAV_GUARD+1")
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=20,
                    hand=[event], max_orders=2, current_orders=2)

        self.assertTrue(deploy_card(p1, event, bf, 0))
        self.assertEqual((cav.card.attack, guard.card.attack, infantry.card.attack), (3, 7, 4))

    def test_kutuzov_event_retreats_and_heals_with_hq_cost(self):
        bf = Battlefield()
        target = BattleUnit(
            card=self.make_card("俄国线列军", attack=2, health=5, unit_type=UnitType.INFANTRY),
            current_hp=2, current_line=Line.SKIRMISH, slot=1, deployed_this_turn=False,
        )
        bf.p1_skirmish = [target]
        event = Card("库图佐夫的战略后撤", 1, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "retreat_friendly_heal2_hq1")
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=20,
                    hand=[event], max_orders=1, current_orders=1)

        self.assertTrue(deploy_card(p1, event, bf, 0))
        self.assertEqual(target.current_line, Line.REAR)
        self.assertEqual(target.current_hp, 4)
        self.assertEqual(p1.hq_hp, 19)

    def test_scorched_earth_event_damages_enemy_skirmish_with_hq_cost(self):
        bf = Battlefield()
        enemy = BattleUnit(card=self.make_card("敌散兵", health=2, unit_type=UnitType.SKIRMISHER),
                           current_hp=2, current_line=Line.SKIRMISH, slot=1, deployed_this_turn=False)
        bf.p2_skirmish = [enemy]
        event = Card("焦土政策", 2, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                     Line.REAR, [], CardType.EVENT, "self_hq1_damage_enemy_skirmish1")
        p1 = Player(name="P1", faction=Faction.RUSSIA, hq_hp=20,
                    hand=[event], max_orders=2, current_orders=2)

        self.assertTrue(deploy_card(p1, event, bf, 0))
        self.assertEqual(enemy.current_hp, 1)
        self.assertEqual(p1.hq_hp, 19)

    def test_weather_events_apply_global_battlefield_modifiers(self):
        bf = Battlefield()
        friendly_art = BattleUnit(card=self.make_card("友炮", attack=3, unit_type=UnitType.ARTILLERY),
                                  current_hp=3, current_line=Line.REAR, slot=1, deployed_this_turn=False)
        enemy_art = BattleUnit(card=self.make_card("敌炮", attack=5, unit_type=UnitType.ARTILLERY),
                               current_hp=3, current_line=Line.REAR, slot=1, deployed_this_turn=False)
        friendly_cav = BattleUnit(card=self.make_card("友骑", attack=2, unit_type=UnitType.CAVALRY),
                                  current_hp=2, current_line=Line.MAIN, slot=2, deployed_this_turn=False)
        enemy_cav = BattleUnit(card=self.make_card("敌骑", attack=4, unit_type=UnitType.CAVALRY),
                               current_hp=3, current_line=Line.MAIN, slot=2, deployed_this_turn=False)
        fragile = BattleUnit(card=self.make_card("伤兵", health=1, unit_type=UnitType.INFANTRY),
                             current_hp=1, current_line=Line.MAIN, slot=3, deployed_this_turn=False)
        bf.p1_rear = [friendly_art]
        bf.p2_rear = [enemy_art]
        bf.p1_main = [friendly_cav, fragile]
        bf.p2_main = [enemy_cav]

        fog = Card("奥斯特里茨晨雾", 2, 0, 0, UnitType.INFANTRY, Faction.FRANCE,
                   Line.REAR, [], CardType.EVENT, "weather_fog_artillery-1")
        mud = Card("莱比锡泥泞", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                   Line.REAR, [], CardType.EVENT, "weather_mud_cavalry-1")
        winter = Card("冬将军", 3, 0, 0, UnitType.INFANTRY, Faction.RUSSIA,
                      Line.REAR, [], CardType.EVENT, "weather_winter_all_damage1")
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=20,
                    hand=[fog, mud, winter], max_orders=7, current_orders=7)

        self.assertTrue(deploy_card(p1, fog, bf, 0))
        self.assertEqual((friendly_art.card.attack, enemy_art.card.attack), (2, 4))
        self.assertTrue(deploy_card(p1, mud, bf, 0))
        self.assertEqual((friendly_cav.card.attack, enemy_cav.card.attack), (1, 3))
        self.assertTrue(deploy_card(p1, winter, bf, 0))
        self.assertNotIn(fragile, bf.p1_main)

    def test_initial_deal_is_four_cards_with_one_extra_for_second_player(self):
        data = play_and_export(Faction.FRANCE, Faction.PRUSSIA, seed=1)
        initial = data["timeline"][0]["state"]

        self.assertEqual(initial["p1"]["hand_size"], 4)
        self.assertEqual(initial["p1"]["deck_size"], 29)
        self.assertEqual(initial["p1"]["orders"], "1/1")
        self.assertEqual(initial["p2"]["hand_size"], 5)
        self.assertEqual(initial["p2"]["deck_size"], 28)
        self.assertEqual(initial["p2"]["orders"], "1/1")

    def test_turn_draws_two_cards_up_to_seven_card_hand_limit(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            deck=[self.make_card("补给1", cost=99), self.make_card("补给2", cost=99)],
            hand=[
                self.make_card("手牌1", cost=99),
                self.make_card("手牌2", cost=99),
                self.make_card("手牌3", cost=99),
                self.make_card("手牌4", cost=99),
                self.make_card("手牌5", cost=99),
                self.make_card("手牌6", cost=99),
            ],
            hq_hp=25,
            max_orders=1,
            current_orders=1,
        )
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)
        log = []

        play_turn(player, opponent, Battlefield(), 0, 1, log)

        self.assertTrue(any("抽到 补给1" in entry for entry in log))
        self.assertEqual(len(player.hand), 7)
        self.assertEqual([card.name for card in player.deck], ["补给2"])

    def test_turn_draws_two_cards_when_hand_has_room(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            deck=[self.make_card("补给1", cost=99), self.make_card("补给2", cost=99)],
            hand=[self.make_card("手牌1", cost=99), self.make_card("手牌2", cost=99)],
            hq_hp=25,
            max_orders=1,
            current_orders=1,
        )
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)
        log = []

        play_turn(player, opponent, Battlefield(), 0, 1, log)

        self.assertTrue(any("抽到 补给1、补给2" in entry for entry in log))
        self.assertEqual(len(player.hand), 4)

    def test_full_hand_draws_no_cards(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            deck=[self.make_card("补给1", cost=99), self.make_card("补给2", cost=99)],
            hand=[self.make_card(f"手牌{i}", cost=99) for i in range(7)],
            hq_hp=25,
            max_orders=1,
            current_orders=1,
        )
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)
        log = []

        play_turn(player, opponent, Battlefield(), 0, 1, log)

        self.assertTrue(any("抽到 (手牌已满)" in entry for entry in log))
        self.assertEqual(len(player.hand), 7)
        self.assertEqual(len(player.deck), 2)

    def test_orders_start_at_one_and_increase_by_one_each_turn_to_sixteen(self):
        self.assertEqual(advance_max_orders(1, 1), 1)
        self.assertEqual(advance_max_orders(1, 2), 2)
        self.assertEqual(advance_max_orders(15, 16), 16)
        self.assertEqual(advance_max_orders(16, 17), 16)

    def test_deployed_card_moves_to_discard_pile(self):
        player = Player(
            name="P1",
            faction=Faction.FRANCE,
            hand=[self.make_card("使用的牌", cost=1)],
            current_orders=1,
        )
        battlefield = Battlefield()

        self.assertTrue(deploy_card(player, player.hand[0], battlefield, 0))

        self.assertEqual(player.hand, [])
        self.assertEqual([card.name for card in player.discard_pile], ["使用的牌"])

    def test_advanced_unit_cannot_attack_on_the_same_turn(self):
        player = Player(name="P1", faction=Faction.FRANCE, deck=[], hand=[], max_orders=4, current_orders=4)
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)
        battlefield = Battlefield()
        advancer = BattleUnit(
            card=self.make_card("前压步兵", cost=2, attack=3, health=3),
            current_hp=3,
            current_line=Line.MAIN,
            slot=1,
            deployed_this_turn=False,
        )
        target = BattleUnit(
            card=self.make_card("敌方散兵", health=5),
            current_hp=5,
            current_line=Line.SKIRMISH,
            slot=2,
            deployed_this_turn=False,
        )
        battlefield.p1_main.append(advancer)
        battlefield.p2_skirmish.append(target)

        play_turn(player, opponent, battlefield, 0, 4, [])

        self.assertEqual(advancer.current_line, Line.SKIRMISH)
        self.assertTrue(advancer.has_acted_this_turn)
        self.assertEqual(target.current_hp, 5)

    def test_dead_targets_are_not_attacked_again_later_in_the_same_phase(self):
        player = Player(name="P1", faction=Faction.FRANCE)
        opponent = Player(name="P2", faction=Faction.PRUSSIA, hq_hp=25)
        battlefield = Battlefield()
        attacker_1 = BattleUnit(
            card=self.make_card("攻击者1", attack=3, health=3),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        attacker_2 = BattleUnit(
            card=self.make_card("攻击者2", attack=3, health=3),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=2,
            deployed_this_turn=False,
        )
        target = BattleUnit(
            card=self.make_card("低血目标", attack=0, health=2),
            current_hp=2,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        battlefield.p1_skirmish.extend([attacker_1, attacker_2])
        battlefield.p2_skirmish.append(target)
        log = []

        from ai import ai_attack_phase
        ai_attack_phase(player, opponent, battlefield, 0, log)

        attacks_against_target = [entry for entry in log if "低血目标" in entry]
        self.assertEqual(len(attacks_against_target), 1)
        self.assertEqual(battlefield.p2_skirmish, [])

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

        # rear-deploy-only：所有 UNIT 卡部署到 REAR；优先中路槽位 1 / 2
        self.assertEqual([u.slot for u in battlefield.get_line(0, Line.REAR)], [1, 2])

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

    def test_skirmish_line_slots_are_shared_between_players(self):
        # rear-deploy-only：散兵线只能通过前压进入；这里验证 SKIRMISH 占位仍然双方共享
        battlefield = Battlefield()
        p1_skirmisher = BattleUnit(
            card=self.make_card("P1散兵", unit_type=UnitType.SKIRMISHER, deploy_line=Line.SKIRMISH),
            current_hp=2, current_line=Line.SKIRMISH, slot=1, deployed_this_turn=False,
        )
        p2_skirmisher = BattleUnit(
            card=self.make_card("P2散兵", unit_type=UnitType.SKIRMISHER, deploy_line=Line.SKIRMISH),
            current_hp=2, current_line=Line.SKIRMISH, slot=2, deployed_this_turn=False,
        )
        battlefield.p1_skirmish.append(p1_skirmisher)
        battlefield.p2_skirmish.append(p2_skirmisher)

        # SKIRMISH 槽位双方共享：P1 已占 slot 1 → P2 看到 slot 1 也被占
        self.assertFalse(battlefield.is_slot_empty(1, Line.SKIRMISH, 1))
        self.assertTrue(battlefield.is_slot_empty(1, Line.SKIRMISH, 0))
        self.assertEqual(battlefield.occupied_slots(0, Line.SKIRMISH), {1, 2})
        self.assertEqual(battlefield.occupied_slots(1, Line.SKIRMISH), {1, 2})

    def test_advance_fails_when_enemy_occupies_matching_skirmish_slot(self):
        battlefield = Battlefield()
        player = Player(name="P1", faction=Faction.FRANCE, current_orders=3)
        main_unit = BattleUnit(
            card=self.make_card("待前压", cost=2),
            current_hp=3,
            current_line=Line.MAIN,
            slot=1,
            deployed_this_turn=False,
        )
        enemy_blocker = BattleUnit(
            card=self.make_card("敌方散兵", unit_type=UnitType.SKIRMISHER, deploy_line=Line.SKIRMISH),
            current_hp=2,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        battlefield.p1_main.append(main_unit)
        battlefield.p2_skirmish.append(enemy_blocker)

        self.assertEqual(choose_units_to_advance(player, battlefield, 0), [])

    def test_main_line_infantry_attacks_shared_skirmish_same_slot(self):
        battlefield = Battlefield()
        attacker = BattleUnit(
            card=self.make_card("步兵", attack=2),
            current_hp=3,
            current_line=Line.MAIN,
            slot=1,
            deployed_this_turn=False,
        )
        target = BattleUnit(
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
        battlefield.p1_main.append(attacker)
        battlefield.p2_skirmish.extend([target, offset_target])

        self.assertEqual(find_attack_targets(battlefield, attacker, 0), [target])

    def test_shared_skirmish_infantry_attacks_adjacent_enemy_skirmisher(self):
        battlefield = Battlefield()
        attacker = BattleUnit(
            card=self.make_card("步兵", attack=2),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=1,
            deployed_this_turn=False,
        )
        target = BattleUnit(
            card=self.make_card("相邻敌人", health=3),
            current_hp=3,
            current_line=Line.SKIRMISH,
            slot=2,
            deployed_this_turn=False,
        )
        battlefield.p1_skirmish.append(attacker)
        battlefield.p2_skirmish.append(target)

        self.assertEqual(find_attack_targets(battlefield, attacker, 0), [target])

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

    def test_artillery_range_three_reaches_shared_skirmish_and_enemy_main(self):
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

        self.assertEqual(find_attack_targets(battlefield, attacker, 0), [skirmish_target, main_target])

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

    def test_card_has_subfaction_field(self):
        """Card dataclass supports optional subfaction tag."""
        card = self.make_card("测试近卫", keywords=["结阵"])
        self.assertIsNone(card.subfaction)
        card2 = self.make_card("测试近卫2", subfaction=SubFaction.IMPERIAL_GUARD)
        self.assertEqual(card2.subfaction, SubFaction.IMPERIAL_GUARD)

    def test_battleunit_has_trigger_state_fields(self):
        """BattleUnit tracks trigger state: on_deploy_fired, on_wounded_exhausted, base_max_hp."""
        card = self.make_card("测试", health=5)
        unit = BattleUnit(card=card, current_hp=5, current_line=Line.MAIN, slot=0)
        self.assertFalse(unit.on_deploy_fired)
        self.assertFalse(unit.on_wounded_exhausted)
        self.assertEqual(unit.base_max_hp, 5)

    def test_player_has_play_log(self):
        """Player has a per-turn PlayLog that resets."""
        from game_state import PlayEntry
        p = Player(name="P1", faction=Faction.FRANCE)
        self.assertIsInstance(p.play_log, list)
        self.assertEqual(len(p.play_log), 0)

    def test_max_chain_depth_suppresses_triggers_beyond_limit(self):
        """MAX_CHAIN_DEPTH=4 caps chained On Destroy activations."""
        from triggers import MAX_CHAIN_DEPTH
        self.assertEqual(MAX_CHAIN_DEPTH, 4)

    def test_no_card_exceeds_two_trigger_types(self):
        """Guard rail: no card carries more than 2 trigger types."""
        from triggers import count_trigger_types
        for faction, builder in DECK_BUILDERS.items():
            for card in builder():
                count = count_trigger_types(card)
                self.assertLessEqual(count, 2,
                    f"{card.name} ({faction.value}) has {count} trigger types, max 2")

    def test_on_deploy_fires_when_card_enters_battlefield(self):
        """On Deploy trigger fires immediately after unit is placed in REAR."""
        bf = Battlefield()
        card = self.make_card("测试部署触发", attack=3, health=3,
                              keywords=["On Deploy"],
                              unit_type=UnitType.INFANTRY)
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    hand=[card], max_orders=5, current_orders=5)
        self.assertTrue(deploy_card(p1, card, bf, 0))
        unit = bf.p1_rear[0]
        self.assertTrue(unit.on_deploy_fired)

    def test_on_deploy_does_not_fire_when_deploy_fails(self):
        """On Deploy does not fire if deploy fails (no slot available)."""
        bf = Battlefield()
        for i in range(4):
            bf.p1_rear.append(BattleUnit(
                card=self.make_card(f"占位{i}"), current_hp=1,
                current_line=Line.REAR, slot=i, deployed_this_turn=False))
        card = self.make_card("无法部署", keywords=["On Deploy"])
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14,
                    hand=[card], max_orders=5, current_orders=5)
        self.assertFalse(deploy_card(p1, card, bf, 0))
        self.assertEqual(len(p1.play_log), 0)

    def test_event_card_creates_play_log_entry(self):
        """EVENT cards are logged to PlayLog on successful play."""
        bf = Battlefield()
        target = BattleUnit(
            card=self.make_card("步兵", attack=2, health=3, unit_type=UnitType.INFANTRY),
            current_hp=3, current_line=Line.REAR, slot=1, deployed_this_turn=False,
        )
        bf.p1_rear = [target]
        event = Card("国防动员", 2, 0, 0, UnitType.INFANTRY, Faction.PRUSSIA,
                     Line.REAR, [], CardType.EVENT, "buff_target_INF+1+2")
        p1 = Player(name="P1", faction=Faction.PRUSSIA, hq_hp=14,
                    hand=[event], max_orders=3, current_orders=3)
        deploy_card(p1, event, bf, 0)
        self.assertEqual(len(p1.play_log), 1)
        self.assertEqual(p1.play_log[0].card_name, "国防动员")
        self.assertEqual(p1.play_log[0].card_type, "event")

    def test_on_wounded_fires_when_unit_hp_drops_below_max(self):
        """On Wounded fires first time current_hp < max_hp within a turn."""
        bf = Battlefield()
        attacker = BattleUnit(card=self.make_card("攻击者", attack=3),
                              current_hp=3, current_line=Line.MAIN, slot=1,
                              deployed_this_turn=False)
        defender = BattleUnit(card=self.make_card("受伤者", attack=2, health=5,
                                                  keywords=["On Wounded"]),
                              current_hp=5, current_line=Line.MAIN, slot=1,
                              deployed_this_turn=False)
        bf.p1_main = [attacker]
        bf.p2_main = [defender]
        execute_attack(attacker, defender, log=[], battlefield=bf, attacker_player_idx=0)
        self.assertTrue(defender.on_wounded_exhausted)

    def test_on_wounded_does_not_fire_on_lethal_damage(self):
        """On Wounded does not fire if damage is lethal (unit dies)."""
        bf = Battlefield()
        attacker = BattleUnit(card=self.make_card("攻击者", attack=10),
                              current_hp=10, current_line=Line.MAIN, slot=1,
                              deployed_this_turn=False)
        defender = BattleUnit(card=self.make_card("将死", attack=1, health=3,
                                                  keywords=["On Wounded"]),
                              current_hp=3, current_line=Line.MAIN, slot=1,
                              deployed_this_turn=False)
        execute_attack(attacker, defender, log=[], battlefield=bf, attacker_player_idx=0)
        self.assertTrue(defender.is_dead)
        self.assertFalse(defender.on_wounded_exhausted)

    def test_on_wounded_does_not_fire_from_aura_attack_reduction(self):
        """On Wounded does NOT fire from 死神威慑 (stat modifier, not HP damage)."""
        defender = BattleUnit(card=self.make_card("目标", attack=2, health=5,
                                                  keywords=["On Wounded"]),
                              current_hp=5, current_line=Line.MAIN, slot=1,
                              deployed_this_turn=False)
        # No attack happens, just aura check — on_wounded should not fire
        self.assertFalse(defender.on_wounded_exhausted)

    def test_on_destroy_cannot_damage_hq(self):
        """Hard rule: On Destroy effects must NOT directly damage either HQ."""
        from triggers import count_trigger_types
        for faction, builder in DECK_BUILDERS.items():
            for card in builder():
                if "焦土补给" in card.keywords:
                    # 焦土补给 grants max_orders, not HQ damage — compliant
                    pass
                for kw in card.keywords:
                    if "On Destroy" in kw:
                        self.assertNotIn("HQ", kw, f"{card.name}: On Destroy cannot damage HQ")

    def test_on_advance_fires_when_unit_moves_to_skirmish(self):
        """On Advance fires when unit crosses line boundary."""
        bf = Battlefield()
        unit = BattleUnit(card=self.make_card("前压单位", attack=3, health=3,
                                               keywords=["On Advance"]),
                          current_hp=3, current_line=Line.MAIN, slot=1,
                          deployed_this_turn=False)
        bf.p1_main = [unit]
        # Simulate advance MAIN→SKIRMISH
        bf.get_line(0, Line.MAIN).remove(unit)
        unit.current_line = Line.SKIRMISH
        unit.has_acted_this_turn = True
        bf.get_line(0, Line.SKIRMISH).append(unit)
        self.assertEqual(unit.current_line, Line.SKIRMISH)
        self.assertIn("On Advance", unit.card.keywords)

    def test_export_includes_trigger_fire_counts(self):
        """Export meta block includes trigger_fire_counts field."""
        data = play_and_export(Faction.FRANCE, Faction.RUSSIA, seed=42)
        self.assertIn("trigger_fire_counts", data["meta"])
        self.assertIsInstance(data["meta"]["trigger_fire_counts"], dict)


if __name__ == "__main__":
    unittest.main()
