import unittest
from unittest.mock import patch

from app.llm import build_prompt_template
from app.planner import build_plan


class PlannerTests(unittest.TestCase):
    def test_build_plan_uses_llm_generated_tasks(self):
        llm_payload = {
            "document_type": "Technical Design",
            "assumptions": ["A phased rollout is assumed."],
            "tasks": [
                {"id": 1, "title": "Design Architecture", "description": "Create the high-level system architecture."},
                {"id": 2, "title": "Design Database", "description": "Define entities and relationships."},
            ],
        }

        with patch("app.planner.try_local_llm", return_value=llm_payload):
            plan = build_plan("Draft a technical design for an AI support platform", "Business Proposal")

        self.assertEqual(plan["document_type"], "Technical Design")
        self.assertEqual(plan["assumptions"], ["A phased rollout is assumed."])
        self.assertEqual(len(plan["tasks"]), 2)
        self.assertEqual(plan["tasks"][0]["title"], "Design Architecture")

    def test_build_plan_falls_back_to_document_type_when_llm_is_unavailable(self):
        with patch("app.planner.try_local_llm", return_value={}):
            plan = build_plan("Create a meeting summary for the launch review", "Business Proposal")

        self.assertEqual(plan["document_type"], "Meeting Minutes")
        self.assertTrue(plan["tasks"])
        self.assertTrue(plan["assumptions"])

    def test_planner_prompt_guides_document_specific_task_lists(self):
        prompt = build_prompt_template("Technical Design", "Draft a technical design for an AI support platform", "AI support platform")

        self.assertIn("document-type-specific", prompt.lower())
        self.assertIn("technical design", prompt.lower())
        self.assertIn("executive summary", prompt.lower())
        self.assertIn("high-level architecture", prompt.lower())
        self.assertIn("deployment", prompt.lower())


if __name__ == "__main__":
    unittest.main()
