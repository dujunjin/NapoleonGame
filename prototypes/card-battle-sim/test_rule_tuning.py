import unittest

from cards import Card, CardType, Faction, Line, UnitType
from cards import DECK_BUILDERS
from combat import execute_attack, find_attack_targets, effective_attack
from game import deploy_card, play_turn, advance_max_orders, MAX_ORDERS, STARTING_HQ_HP, MAX_TURNS
from export_match import play_and_export
from ai import choose_units_to_advance, ai_attack_phase
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

    def test_all_faction_decks_have_thirty_cards(self):
        self.assertEqual({faction: len(builder()) for faction, builder in DECK_BUILDERS.items()}, {
            Faction.FRANCE: 30,
            Faction.PRUSSIA: 30,
            Faction.RUSSIA: 30,
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

    def test_prussia_has_two_event_cards(self):
        prussia = DECK_BUILDERS[Faction.PRUSSIA]()
        events = [c for c in prussia if c.card_type == CardType.EVENT]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].name, "国防动员")
        self.assertEqual(events[0].cost, 2)
        self.assertEqual(events[0].event_effect, "buff_target_INF+1+2")

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

    def test_initial_deal_is_four_cards_with_one_extra_for_second_player(self):
        data = play_and_export(Faction.FRANCE, Faction.PRUSSIA, seed=1)
        initial = data["timeline"][0]["state"]

        self.assertEqual(initial["p1"]["hand_size"], 4)
        self.assertEqual(initial["p1"]["deck_size"], 26)
        self.assertEqual(initial["p1"]["orders"], "1/1")
        self.assertEqual(initial["p2"]["hand_size"], 5)
        self.assertEqual(initial["p2"]["deck_size"], 25)
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


if __name__ == "__main__":
    unittest.main()
