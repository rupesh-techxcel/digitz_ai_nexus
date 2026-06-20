import json
import unittest
from unittest.mock import patch

import frappe

from digitz_ai_nexus.engine.retrieval import get_candidate_chunks
from digitz_ai_nexus.services.semantic_index import (
    build_llm_prompt,
    make_user_questions,
    validate_question_with_llm,
)


class _AllFieldsMeta:
    @staticmethod
    def has_field(_fieldname):
        return True


class TestSemanticQuestionRouting(unittest.TestCase):
    def test_standalone_question_list_is_not_routing_evidence(self):
        chunk = frappe._dict(
            {
                "chunk_text": (
                    "# Example questions\n"
                    "How is Nexy used as a companion?\n"
                    "What is Nexy?"
                ),
                "entity": "NEXUS AI",
                "topic": "Public Visitor Demo Guidance",
            }
        )

        questions = make_user_questions(chunk)

        self.assertNotIn("How is Nexy used as a companion?", questions)
        self.assertNotIn("What is Nexy?", questions)

    def test_explicit_question_and_answer_can_seed_routing(self):
        chunk = frappe._dict(
            {
                "chunk_text": (
                    "Question: How can I request a demo?\n\n"
                    "Answer: Contact the NEXUS AI team through the website."
                ),
                "entity": "NEXUS AI",
                "topic": "Demo Guidance",
            }
        )

        questions = make_user_questions(chunk)

        self.assertIn("How can I request a demo?", questions)

    def test_generation_prompt_rejects_unanswered_question_lists(self):
        prompt = build_llm_prompt(
            frappe._dict(
                {
                    "chunk_text": "How is Nexy used as a companion?",
                    "context_path": "Public/Demo",
                    "entity": "Visitor QA",
                    "topic": "Demo Guidance",
                }
            )
        )

        self.assertIn("question mentioned in the chunk is not evidence", prompt)
        self.assertIn("Ignore standalone lists", prompt)

    @patch("digitz_ai_nexus.services.semantic_index.frappe.db.set_value")
    @patch("digitz_ai_nexus.services.semantic_index.generate_answer")
    @patch("digitz_ai_nexus.services.semantic_index.frappe.get_doc")
    @patch("digitz_ai_nexus.services.semantic_index.has_semantic_index_doctype")
    def test_rejected_question_is_archived_from_routing(
        self,
        mock_has_index,
        mock_get_doc,
        mock_generate_answer,
        mock_set_value,
    ):
        mock_has_index.return_value = True
        entry = frappe._dict(
            {
                "name": "TEST-QUESTION",
                "entry_type": "User Question",
                "canonical_text": "How is Nexy used as a companion?",
                "knowledge_chunk": "TEST-CHUNK",
                "answer_preview": "Example questions only.",
            }
        )
        entry.meta = _AllFieldsMeta()
        chunk = frappe._dict(
            {
                "name": "TEST-CHUNK",
                "chunk_text": "How is Nexy used as a companion?",
            }
        )
        mock_get_doc.side_effect = [entry, chunk]
        mock_generate_answer.return_value = json.dumps(
            {
                "answer": "",
                "confidence": 0,
                "reason": "The chunk contains no answer evidence.",
            }
        )

        with patch(
            "digitz_ai_nexus.services.semantic_index.frappe.db.exists",
            return_value=True,
        ), patch(
            "digitz_ai_nexus.services.semantic_index.frappe.utils.now_datetime",
            return_value="2026-06-20 00:00:00",
        ):
            result = validate_question_with_llm(entry.name)

        self.assertEqual(result["status"], "rejected")
        updates = mock_set_value.call_args.args[2]
        self.assertEqual(updates["answer_review_status"], "Rejected")
        self.assertEqual(updates["disabled"], 1)
        self.assertEqual(updates["status"], "Archived")

    @patch("digitz_ai_nexus.engine.retrieval.fetch_chunks")
    def test_question_first_fetches_only_referenced_chunks(self, mock_fetch_chunks):
        mock_fetch_chunks.return_value = [
            frappe._dict({"name": "CHUNK-2", "project": ""})
        ]

        rows = get_candidate_chunks(
            {"tenant": "NEXUS-AI"},
            chunk_names=["CHUNK-2", "CHUNK-2"],
        )

        self.assertEqual([row.name for row in rows], ["CHUNK-2"])
        filters = mock_fetch_chunks.call_args.args[0]
        self.assertEqual(filters["name"], ["in", ["CHUNK-2"]])


if __name__ == "__main__":
    unittest.main()
