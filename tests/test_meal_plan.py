import asyncio
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from cookidoo_service import CookidooService


CUSTOM_ID = "01KYP84CSDWKDQPGQQ5MR0KM40"
SECOND_CUSTOM_ID = "01KYP934WGA6JKZNXMPEX7MDPE"


class FakeCalendarApi:
    def __init__(self) -> None:
        self.days = {
            date(2026, 7, 29): {
                "official": ["r460132"],
                "custom": [CUSTOM_ID],
            }
        }
        self.calls: list[tuple] = []
        self.fail_remove_on: date | None = None

    @staticmethod
    def _official_recipe(recipe_id: str):
        return SimpleNamespace(
            id=recipe_id,
            name=f"Official {recipe_id}",
            total_time=1800,
            image=f"https://example.test/{recipe_id}.jpg",
            thumbnail=f"https://example.test/{recipe_id}-thumb.jpg",
            url=f"https://example.test/{recipe_id}",
        )

    @staticmethod
    def _custom_recipe(recipe_id: str):
        return SimpleNamespace(
            id=recipe_id,
            name=f"Custom {recipe_id[-4:]}",
            total_time=2400,
            image=f"https://example.test/{recipe_id}.jpg",
            thumbnail=f"https://example.test/{recipe_id}-thumb.jpg",
            url=f"https://example.test/custom/{recipe_id}",
        )

    async def get_recipes_in_calendar_week(self, requested_day):
        week_start = requested_day
        result = []
        for calendar_date, values in sorted(self.days.items()):
            if not week_start <= calendar_date <= week_start.fromordinal(
                week_start.toordinal() + 6
            ):
                continue
            result.append(
                SimpleNamespace(
                    id=calendar_date.isoformat(),
                    title=calendar_date.strftime("%d.%m.%Y"),
                    recipes=[
                        self._official_recipe(recipe_id)
                        for recipe_id in values["official"]
                    ],
                    customer_recipe_ids=list(values["custom"]),
                )
            )
        return result

    async def get_custom_recipe(self, recipe_id):
        return self._custom_recipe(recipe_id)

    async def add_recipes_to_calendar(self, calendar_date, recipe_ids):
        self.calls.append(("add_official", calendar_date, list(recipe_ids)))
        day = self.days.setdefault(
            calendar_date,
            {"official": [], "custom": []},
        )
        day["official"].extend(
            recipe_id
            for recipe_id in recipe_ids
            if recipe_id not in day["official"]
        )

    async def add_custom_recipes_to_calendar(self, calendar_date, recipe_ids):
        self.calls.append(("add_custom", calendar_date, list(recipe_ids)))
        day = self.days.setdefault(
            calendar_date,
            {"official": [], "custom": []},
        )
        day["custom"].extend(
            recipe_id
            for recipe_id in recipe_ids
            if recipe_id not in day["custom"]
        )

    async def remove_recipe_from_calendar(self, calendar_date, recipe_id):
        self.calls.append(("remove_official", calendar_date, recipe_id))
        if self.fail_remove_on == calendar_date:
            raise RuntimeError("simulated removal failure")
        self.days[calendar_date]["official"].remove(recipe_id)

    async def remove_custom_recipe_from_calendar(self, calendar_date, recipe_id):
        self.calls.append(("remove_custom", calendar_date, recipe_id))
        if self.fail_remove_on == calendar_date:
            raise RuntimeError("simulated removal failure")
        self.days[calendar_date]["custom"].remove(recipe_id)


def service_with_fake_api() -> tuple[CookidooService, FakeCalendarApi]:
    api = FakeCalendarApi()
    service = CookidooService("test@example.com", "secret")
    service._api_client = api

    async def delete_request(calendar_date, recipe_id, source):
        if source == "official":
            await api.remove_recipe_from_calendar(calendar_date, recipe_id)
        else:
            await api.remove_custom_recipe_from_calendar(calendar_date, recipe_id)

    service._delete_meal_plan_recipe_request = AsyncMock(
        side_effect=delete_request
    )
    return service, api


def test_get_meal_plan_week_fills_empty_days_and_resolves_custom_ids() -> None:
    async def run():
        service, _ = service_with_fake_api()
        result = await service.get_meal_plan_week(date(2026, 7, 29))

        assert result["week_start"] == "2026-07-29"
        assert result["week_end"] == "2026-08-04"
        assert len(result["days"]) == 7

        planned_day = result["days"][0]
        assert planned_day["date"] == "2026-07-29"
        assert [recipe["source"] for recipe in planned_day["recipes"]] == [
            "official",
            "custom",
        ]
        assert planned_day["recipes"][1]["name"] == f"Custom {CUSTOM_ID[-4:]}"
        assert result["summary"]["recipe_count"] == 2

    asyncio.run(run())


def test_add_meal_plan_recipes_partitions_mixed_sources() -> None:
    async def run():
        service, api = service_with_fake_api()
        result = await service.add_meal_plan_recipes(
            date(2026, 7, 30),
            ["r417685", SECOND_CUSTOM_ID, "r417685"],
        )

        assert ("add_official", date(2026, 7, 30), ["r417685"]) in api.calls
        assert (
            "add_custom",
            date(2026, 7, 30),
            [SECOND_CUSTOM_ID],
        ) in api.calls
        assert result["day"]["recipe_count"] == 2

    asyncio.run(run())


def test_remove_meal_plan_recipe_uses_custom_endpoint() -> None:
    async def run():
        service, api = service_with_fake_api()
        result = await service.remove_meal_plan_recipe(
            date(2026, 7, 29),
            CUSTOM_ID,
        )

        assert (
            "remove_custom",
            date(2026, 7, 29),
            CUSTOM_ID,
        ) in api.calls
        assert [recipe["id"] for recipe in result["day"]["recipes"]] == [
            "r460132"
        ]

    asyncio.run(run())


def test_move_meal_plan_recipe_rolls_back_target_when_source_removal_fails() -> None:
    async def run():
        service, api = service_with_fake_api()
        api.fail_remove_on = date(2026, 7, 29)

        with pytest.raises(RuntimeError, match="simulated removal failure"):
            await service.move_meal_plan_recipe(
                CUSTOM_ID,
                date(2026, 7, 29),
                date(2026, 7, 30),
            )

        assert CUSTOM_ID not in api.days[date(2026, 7, 30)]["custom"]
        assert CUSTOM_ID in api.days[date(2026, 7, 29)]["custom"]

    asyncio.run(run())


def test_unknown_recipe_id_requires_an_explicit_source() -> None:
    with pytest.raises(ValueError, match="Cannot infer"):
        CookidooService._meal_plan_recipe_source("not-a-known-id")
