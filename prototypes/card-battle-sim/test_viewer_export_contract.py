import re
import unittest
from pathlib import Path

from cards import Faction
from export_match import play_and_export


VIEWER_HTML = Path(__file__).with_name("viewer.html").read_text(encoding="utf-8")


class ViewerExportContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = play_and_export(Faction.FRANCE, Faction.RUSSIA, 42)

    def test_event_cards_export_as_event_actions(self):
        event_steps = [
            step for step in self.data["timeline"]
            if self._last_action_log(step).lstrip().startswith("📜")
        ]
        self.assertGreater(len(event_steps), 0)
        self.assertTrue(all(step["action"] == "event" for step in event_steps))

    @staticmethod
    def _last_action_log(step):
        for line in reversed(step.get("log", [])):
            text = line.strip()
            if text.startswith(("▶", "📜", "⇒", "💥", "⚔")):
                return text
        return ""

    def test_units_have_unique_dom_key_in_snapshots(self):
        seen_uid = False
        for step in self.data["timeline"]:
            for side in ("p1", "p2"):
                for line in ("rear", "main", "skirmish"):
                    for unit in step["state"][side][line]:
                        self.assertIn("uid", unit)
                        self.assertRegex(unit["uid"], r"^P[12]\|")
                        seen_uid = True
        self.assertTrue(seen_uid)

    def test_attack_events_include_owner_and_position_identity(self):
        attack_steps = [
            step for step in self.data["timeline"]
            if step.get("attack_event")
        ]
        self.assertGreater(len(attack_steps), 0)
        for step in attack_steps:
            event = step["attack_event"]
            self.assertIn("owner", event["attacker"])
            self.assertIn(event["attacker"]["owner"], ("p1", "p2"))
            self.assertIn("line", event["attacker"])
            self.assertIn("slot", event["attacker"])
            if event["defender"]["line"] != "hq":
                self.assertIn("owner", event["defender"])
                self.assertIn(event["defender"]["owner"], ("p1", "p2"))

    def test_viewer_uses_position_identity_for_attack_elements(self):
        self.assertIn("function findUnitElementForAttack", VIEWER_HTML)
        self.assertNotRegex(
            VIEWER_HTML,
            re.compile(r"const atkEl = findUnitElementByName\\(getAttackerName\\(attackEvent\\)\\)"),
        )

    def test_viewer_has_shaken_rendering_hooks(self):
        self.assertIn("is-shaken", VIEWER_HTML)
        self.assertIn("ucard-status-shaken", VIEWER_HTML)
        self.assertIn("u.is_shaken", VIEWER_HTML)
        self.assertIn("动摇", VIEWER_HTML)

    def test_viewer_hq_target_depends_on_active_player(self):
        self.assertIn("const hqTarget = getHqTargetElement(node.active_player)", VIEWER_HTML)
        self.assertNotIn(
            'hqEnemy.classList.toggle("hq-target", node.action === "hq_attack")',
            VIEWER_HTML,
        )

    def test_timeline_steps_have_stable_action_metadata(self):
        for index, step in enumerate(self.data["timeline"]):
            self.assertIn("action", step, f"step {index + 1}")
            self.assertIn("state", step, f"step {index + 1}")
            self.assertIn("turn", step, f"step {index + 1}")
            self.assertIn("active_player", step, f"step {index + 1}")
            if step["action"] in {"deploy", "event", "advance", "attack", "hq_attack"}:
                self.assertIn("action_id", step, f"step {index + 1}")
                self.assertEqual(step["action_id"], index)

    def test_event_steps_include_event_card_and_effect_text(self):
        event_steps = [step for step in self.data["timeline"] if step["action"] == "event"]
        self.assertGreater(len(event_steps), 0)
        for step in event_steps:
            self.assertIn("event_card", step)
            self.assertTrue(step["event_card"])
            self.assertIn("event_effect_text", step)
            self.assertTrue(step["event_effect_text"])

    def test_units_export_action_state_for_honest_ui(self):
        seen_unit = False
        for step in self.data["timeline"]:
            for side in ("p1", "p2"):
                for line in ("rear", "main", "skirmish"):
                    for unit in step["state"][side][line]:
                        seen_unit = True
                        self.assertIn("can_act", unit)
                        self.assertIn("has_acted_this_turn", unit)
                        self.assertIn("deployed_this_turn", unit)
                        self.assertIsInstance(unit["can_act"], bool)
                        self.assertIsInstance(unit["has_acted_this_turn"], bool)
                        self.assertIsInstance(unit["deployed_this_turn"], bool)
        self.assertTrue(seen_unit)

    def test_units_export_shaken_status_for_morale_ui(self):
        seen_unit = False
        for step in self.data["timeline"]:
            for side in ("p1", "p2"):
                for line in ("rear", "main", "skirmish"):
                    for unit in step["state"][side][line]:
                        seen_unit = True
                        self.assertIn("is_shaken", unit)
                        self.assertIsInstance(unit["is_shaken"], bool)
        self.assertTrue(seen_unit)

    def test_state_exports_battlefield_ui_summary(self):
        valid_labels = {"未接敌", "我方压制", "敌方压制", "交战"}
        for step in self.data["timeline"]:
            summary = step["state"].get("ui_summary")
            self.assertIsInstance(summary, dict)
            self.assertIn(summary.get("skirmish_state"), valid_labels)
            self.assertIn("p1_hq_threat", summary)
            self.assertIn("p2_hq_threat", summary)
            self.assertIsInstance(summary["p1_hq_threat"], int)
            self.assertIsInstance(summary["p2_hq_threat"], int)
            self.assertGreaterEqual(summary["p1_hq_threat"], 0)
            self.assertGreaterEqual(summary["p2_hq_threat"], 0)

    def test_export_snapshot_includes_battlefield_situation_key(self):
        """snapshot_battlefield must include battlefield_situation key."""
        from game_state import Player, Battlefield
        from cards import Faction
        from export_match import snapshot_battlefield
        bf = Battlefield()
        bf.current_situation_id = "dense_fog"
        bf.current_situation_started_turn = 3
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        snap = snapshot_battlefield(p1, p2, bf)
        self.assertIn("battlefield_situation", snap)
        self.assertIsNotNone(snap["battlefield_situation"])
        self.assertEqual(snap["battlefield_situation"]["id"], "dense_fog")
        self.assertEqual(snap["battlefield_situation"]["started_turn"], 3)

    def test_export_snapshot_situation_none_when_inactive(self):
        """battlefield_situation is None when no situation active."""
        from game_state import Player, Battlefield
        from cards import Faction
        from export_match import snapshot_battlefield
        bf = Battlefield()
        p1 = Player(name="P1", faction=Faction.FRANCE, hq_hp=14)
        p2 = Player(name="P2", faction=Faction.RUSSIA, hq_hp=14)
        snap = snapshot_battlefield(p1, p2, bf)
        self.assertIn("battlefield_situation", snap)
        self.assertIsNone(snap["battlefield_situation"])

    def test_export_includes_commander_reaction_key(self):
        """Export source must reference commander_reaction."""
        import export_match
        with open(export_match.__file__) as f:
            source = f.read()
        self.assertIn("commander_reaction", source)

    def test_export_includes_damage_modifiers_key(self):
        """Export source must reference damage_modifiers."""
        import export_match
        with open(export_match.__file__) as f:
            source = f.read()
        self.assertIn("damage_modifiers", source)

    def test_viewer_renders_situation_change_in_timeline(self):
        """Viewer HTML must handle battlefield_situation display."""
        self.assertIn("battlefield_situation", VIEWER_HTML)

    def test_viewer_renders_commander_reaction_in_timeline(self):
        """Viewer HTML must handle commander_reaction display."""
        self.assertIn("commander_reaction", VIEWER_HTML)

    def test_timeline_steps_include_commander_reaction_field(self):
        """All timeline steps should have commander_reaction field after enrichment."""
        for step in self.data["timeline"]:
            self.assertIn("commander_reaction", step, f"step {step.get('action_id', '?')}")

    def test_timeline_steps_include_damage_modifiers_field(self):
        """Attack timeline steps should have damage_modifiers field."""
        for step in self.data["timeline"]:
            if step["action"] == "attack" and step.get("attack_event"):
                self.assertIn("damage_modifiers", step)


if __name__ == "__main__":
    unittest.main()
