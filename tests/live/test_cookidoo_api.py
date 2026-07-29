"""Authenticated smoke tests for Cookidoo's external API.

These tests intentionally exercise the real service so API changes are caught
early. They are skipped unless COOKIDOO_LIVE_TESTS=1 is explicitly set.
"""

import asyncio
from datetime import date
import os
import time
from typing import Any, Coroutine

import pytest

from cookidoo_service import CookidooService


REFERENCE_RECIPE_ID = os.getenv("COOKIDOO_LIVE_RECIPE_ID", "r460132")
REQUEST_TIMEOUT_SECONDS = 120

pytestmark = pytest.mark.live


class LiveCookidooContext:
    """Keep one authenticated aiohttp session on one event loop."""

    def __init__(self, email: str, password: str) -> None:
        self.loop = asyncio.new_event_loop()
        self.service = CookidooService(email, password)
        self.api: Any = None

    def run(
        self,
        operation: Coroutine[Any, Any, Any],
        *,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> Any:
        return self.loop.run_until_complete(
            asyncio.wait_for(operation, timeout=timeout)
        )

    def connect(self) -> None:
        self.api = self.run(self.service.login())

    def close(self) -> None:
        self.run(self.service.close(), timeout=30)
        self.loop.close()


@pytest.fixture(scope="module")
def cookidoo() -> LiveCookidooContext:
    if os.getenv("COOKIDOO_LIVE_TESTS") != "1":
        pytest.skip("Set COOKIDOO_LIVE_TESTS=1 to run authenticated API tests")

    email = os.getenv("COOKIDOO_EMAIL")
    password = os.getenv("COOKIDOO_PASSWORD")
    if not email or not password:
        pytest.fail(
            "COOKIDOO_EMAIL and COOKIDOO_PASSWORD are required for live tests"
        )

    context = LiveCookidooContext(email, password)
    context.connect()
    try:
        yield context
    finally:
        context.close()


def test_login_and_official_recipe_contract(
    cookidoo: LiveCookidooContext,
) -> None:
    recipe = cookidoo.run(
        cookidoo.api.get_recipe_details(REFERENCE_RECIPE_ID)
    )

    assert recipe.id == REFERENCE_RECIPE_ID
    assert isinstance(recipe.name, str) and recipe.name
    assert recipe.ingredients
    assert all(
        isinstance(ingredient.name, str) and ingredient.name
        for ingredient in recipe.ingredients
    )


def test_shopping_list_contract(cookidoo: LiveCookidooContext) -> None:
    result = cookidoo.run(
        cookidoo.service.get_shopping_list_ingredients(
            include_owned=True,
            include_additional_items=True,
        )
    )

    assert isinstance(result["recipes"], list)
    assert isinstance(result["ingredients"], list)
    assert isinstance(result["additional_items"], list)
    assert result["summary"]["recipe_count"] == len(result["recipes"])
    assert result["summary"]["ingredient_count"] == len(result["ingredients"])


def test_meal_plan_contract(cookidoo: LiveCookidooContext) -> None:
    requested_day = date.today()
    result = cookidoo.run(
        cookidoo.service.get_meal_plan_week(requested_day)
    )

    assert result["requested_date"] == requested_day.isoformat()
    assert result["week_start"] == requested_day.isoformat()
    assert len(result["days"]) == 7
    assert result["days"][0]["date"] == requested_day.isoformat()
    assert all(
        isinstance(day_payload["recipes"], list)
        for day_payload in result["days"]
    )


def test_image_signature_contract(cookidoo: LiveCookidooContext) -> None:
    signature = cookidoo.run(
        cookidoo.service._get_custom_recipe_image_signature(int(time.time()))
    )

    assert isinstance(signature, str)
    assert len(signature) >= 32


def test_custom_recipe_copy_patch_and_delete(
    cookidoo: LiveCookidooContext,
) -> None:
    if os.getenv("COOKIDOO_LIVE_MUTATIONS") != "1":
        pytest.skip(
            "Set COOKIDOO_LIVE_MUTATIONS=1 to test temporary recipe writes"
        )

    created_recipe_id: str | None = None
    try:
        copied = cookidoo.run(
            cookidoo.api.add_custom_recipe_from(REFERENCE_RECIPE_ID, 4)
        )
        created_recipe_id = copied.id

        cookidoo.run(
            cookidoo.service.update_custom_recipe_ingredients(
                created_recipe_id,
                ["1 г соли — временный API-тест"],
            )
        )
        cookidoo.run(
            cookidoo.service.update_custom_recipe_steps(
                created_recipe_id,
                ["Временная проверка Cookidoo API. Ничего не готовить."],
            )
        )

        fetched = cookidoo.run(
            cookidoo.api.get_custom_recipe(created_recipe_id)
        )
        assert fetched.id == created_recipe_id
        assert fetched.ingredients == ["1 г соли — временный API-тест"]
        assert fetched.instructions == [
            "Временная проверка Cookidoo API. Ничего не готовить."
        ]
    finally:
        if created_recipe_id is not None:
            cookidoo.run(
                cookidoo.api.remove_custom_recipe(created_recipe_id)
            )
