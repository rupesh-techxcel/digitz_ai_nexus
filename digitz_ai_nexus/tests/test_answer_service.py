from frappe.tests.utils import FrappeTestCase

from digitz_ai_nexus.services.answer_service import (
    answer_query,
    RESTRICTED_ANSWER,
)
from digitz_ai_nexus.engine.prompt import SAFE_FALLBACK_ANSWER
from digitz_ai_nexus.api.query import ask


class MockLLMProvider:
    def generate(self, prompt):
        return "Hire Return valuation is handled based on the approved project knowledge."


def fake_allowed_retrieval(payload, query_embedding=None, embedding_provider=None, **kwargs):
    return {
        "results": [
            {
                "chunk": "NKC-TEST-001",
                "knowledge_unit": "NKU-TEST-001",
                "context_path": "ERP/General/Product/DIGITZ ERP/Valuation",
                "business_unit": "ERP Product",
                "project": "ABC Implementation",
                "scope_type": "project",
                "chunk_text": "Hire Return valuation is a project-specific valuation rule.",
                "score": 0.85,
                "final_score": 0.85,
                "vector_score": 0.75,
                "keyword_score": 0.90,
                "priority_score": 0.10,
                "hybrid_score": 0.85,
                "rerank_score": 0.85,
            }
        ],
        "denied": [],
        "query_variants": ["Hire Return valuation"],
        "debug": [],
        "features": {},
        "weights": {},
        "candidate_count": 1,
        "allowed_count": 1,
        "denied_count": 0,
        "retrieval_mode": "hybrid_grounded_rag",
        "project_scope_mode": "with_general",
    }

def fake_no_context_retrieval(payload, query_embedding=None, embedding_provider=None, **kwargs):
    return {
        "results": [],
        "denied": [],
        "query_variants": [payload.get("query")],
        "debug": [],
        "candidate_count": 0,
        "allowed_count": 0,
        "denied_count": 0,
    }


def fake_restricted_retrieval(payload, query_embedding=None, embedding_provider=None, **kwargs):
    return {
        "results": [],
        "denied": [
            {
                "chunk": "NKC-RESTRICTED-001",
                "reason": "Role not allowed",
                "access_policy": "Restricted",
            }
        ],
        "query_variants": [payload.get("query")],
        "debug": [],
        "candidate_count": 1,
        "allowed_count": 0,
        "denied_count": 1,
    }


def base_payload():
    return {
        "query": "Hire Return valuation",
        "business_unit": "ERP Product",
        "project": "ABC Implementation",
        "project_scope_mode": "with_general",
        "response_mode": "qa",
        "user": {
            "user_id": "test@example.com",
            "roles": ["Accounts Manager"],
            "designations": [],
        },
    }


class TestNexusAnswerService(FrappeTestCase):

    def test_allowed_answer_returns_sources(self):
        res = answer_query(
            base_payload(),
            retrieval_fn=fake_allowed_retrieval,
            llm_provider=MockLLMProvider(),
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["access_status"], "allowed")
        self.assertEqual(res["fallback_used"], 0)
        self.assertTrue(res["answer"])
        self.assertGreater(res["confidence"], 0)
        self.assertGreaterEqual(len(res["sources"]), 1)
        self.assertEqual(res["sources"][0]["chunk"], "NKC-TEST-001")

    def test_no_context_returns_safe_fallback(self):
        res = answer_query(
            base_payload(),
            retrieval_fn=fake_no_context_retrieval,
            llm_provider=MockLLMProvider(),
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["access_status"], "no_context")
        self.assertEqual(res["answer"], SAFE_FALLBACK_ANSWER)
        self.assertEqual(res["fallback_used"], 1)
        self.assertEqual(res["sources"], [])

    def test_restricted_response_does_not_leak_sources(self):
        res = answer_query(
            base_payload(),
            retrieval_fn=fake_restricted_retrieval,
            llm_provider=MockLLMProvider(),
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["access_status"], "restricted")
        self.assertEqual(res["answer"], RESTRICTED_ANSWER)
        self.assertEqual(res["fallback_used"], 1)
        self.assertEqual(res["sources"], [])
        self.assertGreaterEqual(len(res["denied"]), 1)

    def test_query_api_returns_log_and_retrieval_debug(self):
        res = ask(
            payload=base_payload(),
            retrieval_fn=fake_allowed_retrieval,
            llm_provider=MockLLMProvider(),
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["access_status"], "allowed")
        self.assertEqual(res["fallback_used"], 0)
        self.assertTrue(res.get("log"))
        self.assertIn("retrieval_debug", res)
        self.assertGreaterEqual(len(res["sources"]), 1)