import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from app.main import app


class AgentEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_standard_business_request_generates_docx(self):
        response = self.client.post(
            "/agent",
            json={
                "request": "Create a concise project proposal for a new AI scheduling assistant for small clinics."
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("document_name", body)
        self.assertTrue(body["document_name"].endswith(".docx"))
        output_path = body["document_path"]
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "rb") as handle:
            document_bytes = handle.read()
        self.assertIn(b"AI scheduling assistant", document_bytes)

    def test_complex_request_uses_assumptions_and_plan(self):
        response = self.client.post(
            "/agent",
            json={
                "request": "Draft a technical design for an AI-powered support platform, but the team size and budget are unclear. Make reasonable assumptions and explain them."
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["plan"]), 1)
        self.assertGreaterEqual(len(body["assumptions"]), 1)


if __name__ == "__main__":
    unittest.main()
