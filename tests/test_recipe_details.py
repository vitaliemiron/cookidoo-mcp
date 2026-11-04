import asyncio
from types import SimpleNamespace

import server


def _run(awaitable):
    return asyncio.run(awaitable)


class FakeRecipeApi:
    async def get_recipe_details(self, recipe_id: str):
        return SimpleNamespace(
            id=recipe_id,
            name="Pan versátil Keto",
            serving_size=12,
            total_time=6900.0,
            difficulty="easy",
            ingredients=[],
        )


def test_format_duration_converts_cookidoo_seconds() -> None:
    assert server._format_duration(1200) == "20 min"
    assert server._format_duration(2400.0) == "40 min"
    assert server._format_duration("3600") == "1 h"
    assert server._format_duration(6900.0) == "1 h 55 min"
    assert server._format_duration(None) == "unknown"


def test_recipe_details_report_total_time_in_minutes(monkeypatch) -> None:
    monkeypatch.setattr(server, "_cookidoo_api", FakeRecipeApi())

    result = _run(server.get_recipe_details("r484575"))

    assert "Total Time: 1 h 55 min\n" in result
    assert "6900" not in result
