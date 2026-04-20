from __future__ import annotations

import unittest
from types import SimpleNamespace

from fasthtml.common import to_xml

from src.components.transactions import transaction_form
from src.models import Account, Category
from src.services.category_recommendation import CategoryRecommendationService


class FakeClient:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.call_count = 0
        self.messages = self

    def create(self, **kwargs):
        self.call_count += 1
        return SimpleNamespace(content=[SimpleNamespace(text=self.response_text)])


class ErrorClient:
    def __init__(self):
        self.messages = self

    def create(self, **kwargs):
        raise RuntimeError("anthropic down")


class CategoryRecommendationServiceTests(unittest.TestCase):
    def setUp(self):
        self.categories = [
            Category(id=1, label="Groceries"),
            Category(id=2, label="Utilities"),
            Category(id=3, label="Transport"),
        ]

    def test_returns_matching_allowed_category(self):
        client = FakeClient('{"category_id": 1, "rationale": "Looks like groceries."}')
        service = CategoryRecommendationService(
            api_key="test-key",
            client_factory=lambda: client,
        )

        result = service.recommend_category("2026-04-19", -4200, "Trader Joe's", self.categories)

        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.category_id, 1)
        self.assertEqual(result.category_label, "Groceries")
        self.assertEqual(client.call_count, 1)

    def test_rejects_unknown_category(self):
        client = FakeClient('{"category_id": 999, "rationale": "Invented."}')
        service = CategoryRecommendationService(
            api_key="test-key",
            client_factory=lambda: client,
        )

        result = service.recommend_category("2026-04-19", -4200, "Trader Joe's", self.categories)

        self.assertFalse(result.has_recommendation)
        self.assertEqual(result.category_id, None)

    def test_matches_by_category_label_when_id_missing(self):
        client = FakeClient('{"category_label": "Groceries", "rationale": "Food purchase."}')
        service = CategoryRecommendationService(
            api_key="test-key",
            client_factory=lambda: client,
        )

        result = service.recommend_category("2026-04-19", -4200, "Trader Joe's", self.categories)

        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.category_id, 1)
        self.assertEqual(result.category_label, "Groceries")

    def test_missing_inputs_skip_outbound_call(self):
        client = FakeClient('{"category_id": 1, "rationale": "Should not be used."}')
        service = CategoryRecommendationService(
            api_key="test-key",
            client_factory=lambda: client,
        )

        result = service.recommend_category("", -4200, "Trader Joe's", self.categories)

        self.assertFalse(result.has_recommendation)
        self.assertEqual(client.call_count, 0)

    def test_api_errors_return_empty_result(self):
        service = CategoryRecommendationService(
            api_key="test-key",
            client_factory=lambda: ErrorClient(),
        )

        result = service.recommend_category("2026-04-19", -4200, "Trader Joe's", self.categories)

        self.assertFalse(result.has_recommendation)


class TransactionFormTests(unittest.TestCase):
    def test_ai_panel_is_hidden_without_api_access(self):
        html = to_xml(
            transaction_form(
                accounts=[Account(id=3, label="Daily Expenses", account_type="expenses")],
                categories=[Category(id=1, label="Groceries")],
                today="2026-04-19",
                last_account_id=3,
                account_type="expenses",
                ai_enabled=False,
            )
        )

        self.assertNotIn('data-testid="transaction-category-recommendation"', html)


if __name__ == "__main__":
    unittest.main()
