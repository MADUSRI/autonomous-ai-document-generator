import unittest
from pathlib import Path

from docx import Document

from app.document_generator import build_document_from_context


class DocumentGeneratorTests(unittest.TestCase):
    def test_build_document_from_context_formats_executor_sections(self):
        context = {
            "request": "Draft a technical design for an AI support platform",
            "document_type": "Technical Design",
            "assumptions": ["A phased rollout is assumed.", "Security review is required."],
            "sections": [
                {
                    "title": "Architecture",
                    "content": "The platform uses a modular service architecture.\n\n- API gateway\n- orchestration service\n- analytics pipeline",
                },
                {
                    "title": "Risks",
                    "content": "Primary risks include integration complexity and data quality issues.",
                },
            ],
        }

        output_path = build_document_from_context(context)

        self.assertTrue(isinstance(output_path, Path))
        self.assertTrue(output_path.exists())

        document = Document(output_path)
        paragraphs = [p.text for p in document.paragraphs]
        joined_text = "\n".join(paragraphs)

        self.assertIn("Technical Design", joined_text)
        self.assertIn("Draft a technical design for an AI support platform", joined_text)
        self.assertIn("A phased rollout is assumed.", joined_text)
        self.assertIn("Security review is required.", joined_text)
        self.assertIn("Architecture", joined_text)
        self.assertIn("The platform uses a modular service architecture.", joined_text)
        self.assertIn("API gateway", joined_text)
        self.assertIn("Risks", joined_text)
        self.assertIn("Primary risks include integration complexity and data quality issues.", joined_text)


if __name__ == "__main__":
    unittest.main()
