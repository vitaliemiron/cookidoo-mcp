import asyncio
from types import SimpleNamespace

import pytest

from cookidoo_service import CookidooService


class FakeShoppingApi:
    async def get_shopping_list_recipes(self):
        return [
            SimpleNamespace(
                id="recipe-1",
                name="Recipe One",
                url="https://example.test/recipe-1",
                image=None,
                thumbnail=None,
                ingredients=[
                    SimpleNamespace(
                        id="ingredient-1",
                        name="Rice",
                        description="200 g rice",
                    ),
                    SimpleNamespace(
                        id="ingredient-2",
                        name="Salt",
                        description="1 tsp salt",
                    ),
                ],
            ),
            SimpleNamespace(
                id="recipe-2",
                name="Recipe Two",
                url="https://example.test/recipe-2",
                image=None,
                thumbnail=None,
                ingredients=[
                    SimpleNamespace(
                        id="ingredient-3",
                        name="Water",
                        description="500 g water",
                    )
                ],
            ),
        ]

    async def get_ingredient_items(self):
        return [
            SimpleNamespace(id="ingredient-1", is_owned=False),
            SimpleNamespace(id="ingredient-2", is_owned=True),
            SimpleNamespace(id="ingredient-3", is_owned=False),
        ]

    async def get_additional_items(self):
        return [
            SimpleNamespace(id="additional-1", name="Napkins", is_owned=False),
            SimpleNamespace(id="additional-2", name="Soap", is_owned=True),
        ]


def service_with_fake_api() -> CookidooService:
    service = CookidooService("test@example.com", "secret")
    service._api_client = FakeShoppingApi()
    return service


def test_shopping_list_is_grouped_and_excludes_owned_by_default() -> None:
    async def run():
        result = await service_with_fake_api().get_shopping_list_ingredients()
        assert result["summary"] == {
            "recipe_count": 2,
            "ingredient_count": 2,
            "additional_item_count": 1,
            "owned_ingredient_count": 1,
            "include_owned": False,
            "filtered_recipe_id": None,
        }
        assert [item["name"] for item in result["ingredients"]] == [
            "Rice",
            "Water",
        ]
        assert result["recipes"][0]["ingredients"][0]["recipe_id"] == "recipe-1"
        assert result["additional_items"][0]["name"] == "Napkins"

    asyncio.run(run())


def test_shopping_list_can_filter_one_recipe_and_include_owned() -> None:
    async def run():
        result = await service_with_fake_api().get_shopping_list_ingredients(
            recipe_id="recipe-1",
            include_owned=True,
            include_additional_items=False,
        )
        assert result["summary"]["recipe_count"] == 1
        assert result["summary"]["ingredient_count"] == 2
        assert result["recipes"][0]["id"] == "recipe-1"
        assert result["additional_items"] == []

    asyncio.run(run())


def test_unknown_shopping_list_recipe_reports_available_ids() -> None:
    async def run():
        with pytest.raises(ValueError, match="recipe-1"):
            await service_with_fake_api().get_shopping_list_ingredients(
                recipe_id="missing"
            )

    asyncio.run(run())
