from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass
from typing import Callable, Optional

from src.models import Category

try:
    import anthropic
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    anthropic = None


DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
logger = logging.getLogger("cashcompass.ai")


@dataclass
class RecommendationResult:
    category_id: Optional[int] = None
    category_label: str = ""
    rationale: str = ""

    @property
    def has_recommendation(self) -> bool:
        return self.category_id is not None and bool(self.category_label)


class CategoryRecommendationService:
    def __init__(
        self,
        api_key: str = "",
        model: str = DEFAULT_ANTHROPIC_MODEL,
        client_factory: Optional[Callable[[], object]] = None,
        mock_response: str = "",
    ):
        self.api_key = (api_key or "").strip()
        self.model = model
        self.mock_response = (mock_response or "").strip()
        self._has_custom_client_factory = client_factory is not None
        self._client_factory = client_factory or self._default_client_factory

    @property
    def is_enabled(self) -> bool:
        if self.mock_response:
            return True
        if self._has_custom_client_factory:
            return True
        return bool(self.api_key and anthropic is not None)

    def recommend_category(
        self,
        date: str,
        amount_cents: int,
        label: str,
        categories: list[Category],
    ) -> RecommendationResult:
        normalized_date = (date or "").strip()
        normalized_label = (label or "").strip()
        if not normalized_date or not normalized_label or amount_cents == 0 or not categories or not self.is_enabled:
            return RecommendationResult()

        allowed_categories = {cat.id: cat.label for cat in categories}
        if self.mock_response:
            return self._parse_response_text(self.mock_response, allowed_categories)

        client = self._client_factory()
        if client is None:
            return RecommendationResult()

        amount_dollars = f"{amount_cents / 100:.2f}"
        prompt_payload = {
            "date": normalized_date,
            "amount_cents": amount_cents,
            "amount_dollars": amount_dollars,
            "description": normalized_label,
            "allowed_categories": [
                {"id": cat.id, "label": cat.label}
                for cat in categories
            ],
        }

        system_prompt = (
            "You recommend one category for a personal finance transaction. "
            "Use only the categories provided. "
            "Return strict JSON with keys category_id and rationale. "
            "If no category is a good match, return {\"category_id\": null, \"rationale\": \"\"}."
        )

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=120,
                temperature=0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(prompt_payload),
                    }
                ],
            )
        except Exception:
            logger.exception("Anthropic category recommendation request failed")
            return RecommendationResult()

        raw_text = self._extract_text(message)
        logger.info("Anthropic raw category recommendation response: %s", raw_text)
        result = self._parse_response_text(raw_text, allowed_categories)
        if result.has_recommendation:
            logger.info(
                "Anthropic category recommendation matched category_id=%s label=%s",
                result.category_id,
                result.category_label,
            )
        else:
            logger.info("Anthropic category recommendation produced no valid match")
        return result

    def _default_client_factory(self):
        if anthropic is None or not self.api_key:
            return None
        return anthropic.Anthropic(api_key=self.api_key)

    @staticmethod
    def _extract_text(message) -> str:
        parts = []
        for block in getattr(message, "content", []) or []:
            text = getattr(block, "text", "")
            if text:
                parts.append(text)
        return "".join(parts).strip()

    @staticmethod
    def _extract_json_object(raw_text: str) -> str:
        text = (raw_text or "").strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return ""
        return text[start:end + 1]

    def _parse_response_text(self, raw_text: str, allowed_categories: dict[int, str]) -> RecommendationResult:
        raw_json = self._extract_json_object(raw_text)
        if not raw_json:
            return RecommendationResult()

        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            return RecommendationResult()

        category_id = None
        raw_category_id = payload.get("category_id")
        try:
            category_id = int(raw_category_id) if raw_category_id is not None else None
        except (TypeError, ValueError):
            category_id = None

        if category_id is None or category_id not in allowed_categories:
            raw_category_label = str(payload.get("category_label") or "").strip()
            if raw_category_label:
                normalized_requested = raw_category_label.casefold()
                for allowed_id, allowed_label in allowed_categories.items():
                    if allowed_label.casefold() == normalized_requested:
                        category_id = allowed_id
                        break

        if category_id is None or category_id not in allowed_categories:
            logger.info("Anthropic category recommendation payload did not match allowed categories: %s", payload)
            return RecommendationResult()

        rationale = str(payload.get("rationale") or "").strip()
        if len(rationale) > 160:
            rationale = rationale[:157].rstrip() + "..."

        return RecommendationResult(
            category_id=category_id,
            category_label=allowed_categories[category_id],
            rationale=rationale,
        )


def build_category_recommendation_service() -> CategoryRecommendationService:
    return CategoryRecommendationService(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        mock_response=os.environ.get("CASHCOMPASS_ANTHROPIC_MOCK_RESPONSE", ""),
    )
