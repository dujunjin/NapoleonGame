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


if __name__ == "__main__":
    unittest.main()
