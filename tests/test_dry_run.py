import asyncio
import json
from pathlib import Path

from PIL import Image

import server


CUSTOM_RECIPE_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"


def _run(awaitable):
    return asyncio.run(awaitable)


def _preview(awaitable) -> dict:
    result = json.loads(_run(awaitable))
    assert result["dry_run"] is True
    assert result["will_mutate"] is False
    assert result["apply"]["instruction"].endswith(
        "dry_run=false to apply it."
    )
    return result


def test_recipe_mutation_dry_runs_validate_without_a_connection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(server, "_cookidoo_service", None)
    monkeypatch.setattr(server, "_cookidoo_api", None)

    copied = _preview(
        server.copy_recipe_to_custom("r460132", servings=6, dry_run=True)
    )
    assert copied["changes"]["servings"] == 6

    steps = _preview(
        server.update_custom_recipe_steps(
            CUSTOM_RECIPE_ID,
            '["Add 100 g water.", "Mix 20 sec/speed 4."]',
            dry_run=True,
        )
    )
    assert steps["changes"]["step_count"] == 2

    ingredients = _preview(
        server.update_custom_recipe_ingredients(
            CUSTOM_RECIPE_ID,
            '["100 g water", "1 tsp salt"]',
            dry_run=True,
        )
    )
    assert ingredients["changes"]["ingredient_count"] == 2

    recipe = _preview(
        server.upload_custom_recipe(
            json.dumps(
                {
                    "name": "Preview soup",
                    "ingredients": ["500 g water"],
                    "steps": ["Add the water."],
                }
            ),
            dry_run=True,
        )
    )
    assert recipe["changes"]["recipe"]["name"] == "Preview soup"

    source = tmp_path / "preview.png"
    Image.new("RGB", (24, 18), "green").save(source)
    image = _preview(
        server.upload_custom_recipe_image(
            CUSTOM_RECIPE_ID,
            str(source),
            dry_run=True,
        )
    )
    assert image["changes"]["normalized_filename"] == "preview.jpg"
    assert image["changes"]["content_type"] == "image/jpeg"


def test_meal_plan_dry_runs_partition_and_describe_operations(
    monkeypatch,
) -> None:
    monkeypatch.setattr(server, "_cookidoo_service", None)

    added = _preview(
        server.add_recipes_to_meal_plan(
            "2026-08-01",
            f"r460132, {CUSTOM_RECIPE_ID}",
            dry_run=True,
        )
    )
    assert added["changes"] == {
        "official_recipe_ids": ["r460132"],
        "custom_recipe_ids": [CUSTOM_RECIPE_ID],
    }

    removed = _preview(
        server.remove_recipe_from_meal_plan(
            "2026-08-01",
            "r460132",
            dry_run=True,
        )
    )
    assert removed["target"]["recipe_source"] == "official"

    moved = _preview(
        server.move_recipe_in_meal_plan(
            CUSTOM_RECIPE_ID,
            "2026-08-01",
            "2026-08-03",
            dry_run=True,
        )
    )
    assert moved["changes"]["add_to_target_first"] is True
    assert moved["changes"]["remove_from_source_after_add"] is True


def test_dry_run_rejects_invalid_inputs_without_mutating(
    monkeypatch,
) -> None:
    monkeypatch.setattr(server, "_cookidoo_service", None)
    monkeypatch.setattr(server, "_cookidoo_api", None)

    bad_date = _run(
        server.add_recipes_to_meal_plan(
            "01-08-2026",
            "r460132",
            dry_run=True,
        )
    )
    assert "expected YYYY-MM-DD" in bad_date

    bad_steps = _run(
        server.update_custom_recipe_steps(
            CUSTOM_RECIPE_ID,
            "not JSON",
            dry_run=True,
        )
    )
    assert bad_steps.startswith("Invalid JSON:")

    missing_image = _run(
        server.upload_custom_recipe_image(
            CUSTOM_RECIPE_ID,
            "/definitely/missing/image.jpg",
            dry_run=True,
        )
    )
    assert "does not exist" in missing_image
