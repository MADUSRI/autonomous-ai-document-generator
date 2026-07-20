import unittest
from unittest.mock import patch

from app.executor import execute_document_generation
from app.reflector import reflect_on_output


class ExecutorTests(unittest.TestCase):
    def test_execute_document_generation_builds_execution_context_from_tasks(self):
        tasks = [
            {"title": "Architecture", "description": "Describe the architecture."},
            {"title": "Risks", "description": "Capture risks and mitigations."},
        ]

        with patch("app.executor.execute_task", side_effect=["Architecture content", "Risk content"]):
            context = execute_document_generation(
                "Draft a technical design for an AI support platform",
                "Technical Design",
                tasks,
                ["A phased rollout is assumed."],
            )

        self.assertEqual(context["request"], "Draft a technical design for an AI support platform")
        self.assertEqual(context["document_type"], "Technical Design")
        self.assertEqual(len(context["sections"]), 2)
        self.assertEqual(context["sections"][0]["title"], "Architecture")
        self.assertEqual(context["sections"][0]["content"], "Architecture content")
        self.assertEqual(context["sections"][1]["title"], "Risks")
        self.assertEqual(context["sections"][1]["content"], "Risk content")

    def test_reflect_on_output_uses_full_execution_context(self):
        execution_context = {
            "request": "Create a technical design for an online food delivery system",
            "document_type": "Technical Design",
            "assumptions": ["A mobile app and web portal are in scope."],
            "sections": [
                {
                    "title": "Architecture",
                    "content": "The architecture includes core services and data stores.",
                },
                {
                    "title": "Risks",
                    "content": "Delivery delays are the main operational risk.",
                },
            ],
        }

        with patch("app.reflector.httpx.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "response": '{"request": "Create a technical design for an online food delivery system", "document_type": "Technical Design", "assumptions": ["A mobile app and web portal are in scope."], "sections": [{"title": "Architecture", "content": "The architecture includes order routing, rider dispatch, and payment services for a food delivery platform."}]}'
            }

            reflected = reflect_on_output(execution_context)

        self.assertIn("execution_context", reflected)
        self.assertEqual(reflected["execution_context"]["document_type"], "Technical Design")
        self.assertEqual(reflected["execution_context"]["sections"][0]["title"], "Architecture")
        self.assertIn("food delivery platform", reflected["execution_context"]["sections"][0]["content"])


if __name__ == "__main__":
    unittest.main()
