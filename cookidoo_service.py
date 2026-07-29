"""
Cookidoo Service

Module to encapsulate all cookidoo-api logic for interacting with the Cookidoo platform.
"""

import os
import asyncio
from datetime import date, timedelta
from io import BytesIO
import json
from pathlib import Path
import re
import time
from typing import Any, Optional

from dotenv import load_dotenv
from aiohttp import ClientSession, FormData
from cookidoo_api import Cookidoo, CookidooConfig
from cookidoo_api.const import REMOVE_RECIPE_FROM_CALENDER_PATH
from cookidoo_api.helpers import (
    get_localization_options,
)
import aiohttp
from PIL import Image, ImageOps, UnidentifiedImageError

from schemas import RecipeIngredient, RecipeStep, ingredient_to_api, step_to_api

CLOUDINARY_API_KEY = "993585863591145"
CLOUDINARY_UPLOAD_PRESET = "prod-customer-recipe-signed"
CLOUDINARY_UPLOAD_URL = (
    "https://api-eu.cloudinary.com/v1_1/vorwerk-users-gc/image/upload"
)
MAX_CUSTOM_RECIPE_IMAGE_BYTES = 10 * 1024 * 1024
DEFAULT_COOKIDOO_COUNTRY = "ro"
DEFAULT_COOKIDOO_LANGUAGE = "en"


def normalize_cookidoo_country(country: str) -> str:
    """Normalize and validate a Cookidoo ISO country code."""

    normalized = country.strip().lower()
    if not re.fullmatch(r"[a-z]{2}", normalized):
        raise ValueError(
            "Invalid COOKIDOO_COUNTRY. Use a two-letter country code such as "
            "'ro', 'de', or 'us'."
        )
    return normalized


def normalize_cookidoo_language(language: str) -> str:
    """Normalize a Cookidoo language tag such as ``en`` or ``pt-BR``."""

    raw_parts = language.strip().replace("_", "-").split("-")
    if not raw_parts or not re.fullmatch(r"[A-Za-z]{2,3}", raw_parts[0]):
        raise ValueError(
            "Invalid COOKIDOO_LANGUAGE. Use a language tag such as 'en', "
            "'de-DE', or 'pt-BR'."
        )

    normalized_parts = [raw_parts[0].lower()]
    for part in raw_parts[1:]:
        if re.fullmatch(r"[A-Za-z]{2}", part):
            normalized_parts.append(part.upper())
        elif re.fullmatch(r"[A-Za-z]{4}", part):
            normalized_parts.append(part.title())
        elif re.fullmatch(r"[0-9]{3}", part):
            normalized_parts.append(part)
        else:
            raise ValueError(
                "Invalid COOKIDOO_LANGUAGE. Use a language tag such as 'en', "
                "'de-DE', or 'pt-BR'."
            )
    return "-".join(normalized_parts)


def load_cookidoo_locale(
    country: str | None = None,
    language: str | None = None,
) -> tuple[str, str]:
    """Load and normalize Cookidoo locale settings.

    Explicit values take precedence over environment variables. If neither is
    supplied, the established international Romanian-account defaults are
    retained for backwards compatibility.
    """

    load_dotenv()
    selected_country = (
        country
        if country is not None
        else os.getenv("COOKIDOO_COUNTRY", DEFAULT_COOKIDOO_COUNTRY)
    )
    selected_language = (
        language
        if language is not None
        else os.getenv("COOKIDOO_LANGUAGE", DEFAULT_COOKIDOO_LANGUAGE)
    )
    return (
        normalize_cookidoo_country(selected_country),
        normalize_cookidoo_language(selected_language),
    )


async def resolve_cookidoo_localization(
    country: str,
    language: str,
):
    """Resolve an exact country/language pair supported by cookidoo-api."""

    options = await get_localization_options(
        country=country,
        language=language,
    )
    if options:
        return options[0]

    country_options = await get_localization_options(country=country)
    if country_options:
        supported_languages = ", ".join(
            sorted({option.language for option in country_options})
        )
        raise ValueError(
            f"Cookidoo does not support language {language!r} for country "
            f"{country!r}. Supported languages for {country!r}: "
            f"{supported_languages}. Set COOKIDOO_LANGUAGE to one of these "
            "values."
        )

    raise ValueError(
        f"Cookidoo does not support country {country!r}. Set "
        "COOKIDOO_COUNTRY to a supported two-letter Cookidoo country code."
    )


def load_cookidoo_credentials() -> tuple[str, str]:
    """
    Load Cookidoo credentials from .env file.

    Returns:
        tuple[str, str]: Email and password

    Raises:
        ValueError: If credentials are not found in environment variables
    """
    load_dotenv()

    email = os.getenv("COOKIDOO_EMAIL")
    password = os.getenv("COOKIDOO_PASSWORD")

    if not email or not password:
        raise ValueError(
            "Missing Cookidoo credentials. Please set COOKIDOO_EMAIL and "
            "COOKIDOO_PASSWORD in your .env file"
        )

    return email, password


class CookidooService:
    """Service class for managing Cookidoo API interactions."""

    def __init__(
        self,
        email: str,
        password: str,
        country: str | None = None,
        language: str | None = None,
    ):
        """
        Initialize the Cookidoo service with credentials.

        Args:
            email: Cookidoo account email
            password: Cookidoo account password
            country: Optional Cookidoo country code. Falls back to
                COOKIDOO_COUNTRY, then ``ro``.
            language: Optional Cookidoo language tag. Falls back to
                COOKIDOO_LANGUAGE, then ``en``.
        """
        self.email = email
        self.password = password
        self.country, self.language = load_cookidoo_locale(country, language)
        self._api_client: Optional[Cookidoo] = None
        self._session: Optional[ClientSession] = None

    async def login(self) -> Cookidoo:
        """
        Authenticate with Cookidoo and return the API client.

        Returns:
            Cookidoo: Authenticated Cookidoo API client

        Raises:
            Exception: If authentication fails
        """
        try:
            localization = await resolve_cookidoo_localization(
                self.country,
                self.language,
            )

            # Create aiohttp ClientSession with a timeout
            self._session = ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            )

            # Create CookidooConfig with credentials
            config = CookidooConfig(
                email=self.email,
                password=self.password,
                localization=localization,
            )

            # Create Cookidoo API client with session and config
            self._api_client = Cookidoo(session=self._session, cfg=config)

            # Perform login (no parameters needed - uses config)
            await self._api_client.login()

            return self._api_client

        except ValueError:
            if self._session:
                await self._session.close()
            raise
        except Exception as e:
            # Clean up session if login fails
            if self._session:
                await self._session.close()
            raise RuntimeError(
                "Failed to authenticate with Cookidoo. Check your credentials "
                "and locale configuration."
            ) from e

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()

    async def get_shopping_list_ingredients(
        self,
        recipe_id: str | None = None,
        include_owned: bool = False,
        include_additional_items: bool = True,
    ) -> dict[str, Any]:
        """
        Return shopping-list ingredients grouped by their source recipe.

        Args:
            recipe_id: Optional exact shopping-list recipe ID to select.
            include_owned: Include ingredients marked as already owned.
            include_additional_items: Include manually added shopping-list items.

        Returns:
            A JSON-ready dictionary containing recipe groups, a flat ingredient
            list, additional items, and summary counts.
        """
        if self._api_client is None:
            raise RuntimeError("Not connected to Cookidoo")

        recipes, ingredient_items, additional_items = await asyncio.gather(
            self._api_client.get_shopping_list_recipes(),
            self._api_client.get_ingredient_items(),
            self._api_client.get_additional_items(),
        )

        ownership_by_id = {
            ingredient.id: ingredient.is_owned for ingredient in ingredient_items
        }
        selected_recipes = (
            [recipe for recipe in recipes if recipe.id == recipe_id]
            if recipe_id
            else recipes
        )
        if recipe_id and not selected_recipes:
            available = ", ".join(f"{recipe.id} ({recipe.name})" for recipe in recipes)
            raise ValueError(
                f"Recipe {recipe_id!r} is not in the shopping list. "
                f"Available recipes: {available or 'none'}"
            )

        recipe_groups: list[dict[str, Any]] = []
        flat_ingredients: list[dict[str, Any]] = []
        owned_count = 0

        for recipe in selected_recipes:
            ingredients: list[dict[str, Any]] = []
            for ingredient in recipe.ingredients:
                is_owned = ownership_by_id.get(ingredient.id, False)
                if is_owned:
                    owned_count += 1
                if is_owned and not include_owned:
                    continue
                item = {
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "description": ingredient.description,
                    "is_owned": is_owned,
                    "recipe_id": recipe.id,
                    "recipe_name": recipe.name,
                }
                ingredients.append(item)
                flat_ingredients.append(item)

            recipe_groups.append(
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "url": recipe.url,
                    "image": recipe.image,
                    "thumbnail": recipe.thumbnail,
                    "ingredient_count": len(ingredients),
                    "ingredients": ingredients,
                }
            )

        additional_payload = []
        if include_additional_items:
            additional_payload = [
                {
                    "id": item.id,
                    "name": item.name,
                    "is_owned": item.is_owned,
                }
                for item in additional_items
                if include_owned or not item.is_owned
            ]

        return {
            "recipes": recipe_groups,
            "ingredients": flat_ingredients,
            "additional_items": additional_payload,
            "summary": {
                "recipe_count": len(recipe_groups),
                "ingredient_count": len(flat_ingredients),
                "additional_item_count": len(additional_payload),
                "owned_ingredient_count": owned_count,
                "include_owned": include_owned,
                "filtered_recipe_id": recipe_id,
            },
        }

    @staticmethod
    def _meal_plan_recipe_source(
        recipe_id: str,
        recipe_source: str = "auto",
    ) -> str:
        """Resolve a calendar recipe to Cookidoo's official/customer source."""

        normalized_source = recipe_source.strip().lower()
        aliases = {
            "auto": "auto",
            "official": "official",
            "cookidoo": "official",
            "custom": "custom",
            "customer": "custom",
        }
        if normalized_source not in aliases:
            raise ValueError(
                "recipe_source must be auto, official, or custom"
            )

        resolved_source = aliases[normalized_source]
        if resolved_source != "auto":
            return resolved_source
        if re.fullmatch(r"r\d+", recipe_id, flags=re.IGNORECASE):
            return "official"
        if re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", recipe_id):
            return "custom"
        raise ValueError(
            f"Cannot infer calendar source for recipe {recipe_id!r}. "
            "Pass recipe_source='official' or recipe_source='custom'."
        )

    @staticmethod
    def _calendar_recipe_payload(recipe: Any, source: str) -> dict[str, Any]:
        """Convert a cookidoo-api calendar/custom recipe to JSON-ready data."""

        return {
            "id": recipe.id,
            "name": recipe.name,
            "source": source,
            "total_time_seconds": getattr(recipe, "total_time", None),
            "image": getattr(recipe, "image", None),
            "thumbnail": getattr(recipe, "thumbnail", None),
            "url": getattr(recipe, "url", None),
        }

    async def get_meal_plan_week(self, day: date) -> dict[str, Any]:
        """Return Cookidoo's complete seven-day meal-plan window.

        Cookidoo omits empty days and, for custom recipes, currently returns
        only IDs. This method fills the missing days and resolves custom IDs to
        their recipe names, images, durations, and URLs. The endpoint treats
        ``day`` as the first day of a rolling seven-day window, matching the
        ``?date=...`` value used by the web planner.
        """

        if self._api_client is None:
            raise RuntimeError("Not connected to Cookidoo")

        calendar_days = await self._api_client.get_recipes_in_calendar_week(day)
        week_start = day
        week_dates = [day + timedelta(days=offset) for offset in range(7)]
        days_by_id = {calendar_day.id: calendar_day for calendar_day in calendar_days}

        custom_ids = list(
            dict.fromkeys(
                recipe_id
                for calendar_day in calendar_days
                for recipe_id in calendar_day.customer_recipe_ids
            )
        )
        resolved_custom: dict[str, dict[str, Any]] = {}
        if custom_ids:
            results = await asyncio.gather(
                *(
                    self._api_client.get_custom_recipe(recipe_id)
                    for recipe_id in custom_ids
                ),
                return_exceptions=True,
            )
            for recipe_id, result in zip(custom_ids, results, strict=True):
                if isinstance(result, BaseException):
                    resolved_custom[recipe_id] = {
                        "id": recipe_id,
                        "name": None,
                        "source": "custom",
                        "total_time_seconds": None,
                        "image": None,
                        "thumbnail": None,
                        "url": None,
                        "resolution_error": str(result),
                    }
                else:
                    resolved_custom[recipe_id] = self._calendar_recipe_payload(
                        result,
                        "custom",
                    )

        payload_days: list[dict[str, Any]] = []
        total_recipe_count = 0
        for calendar_date in week_dates:
            day_key = calendar_date.isoformat()
            calendar_day = days_by_id.get(day_key)
            recipes: list[dict[str, Any]] = []
            seen_recipe_ids: set[str] = set()

            if calendar_day is not None:
                custom_id_set = set(calendar_day.customer_recipe_ids)
                for calendar_recipe in calendar_day.recipes:
                    source = (
                        "custom"
                        if calendar_recipe.id in custom_id_set
                        or re.fullmatch(
                            r"[0-9A-HJKMNP-TV-Z]{26}",
                            calendar_recipe.id,
                        )
                        else "official"
                    )
                    recipes.append(
                        resolved_custom.get(calendar_recipe.id)
                        if source == "custom"
                        and calendar_recipe.id in resolved_custom
                        else self._calendar_recipe_payload(
                            calendar_recipe,
                            source,
                        )
                    )
                    seen_recipe_ids.add(calendar_recipe.id)

                for recipe_id in calendar_day.customer_recipe_ids:
                    if recipe_id not in seen_recipe_ids:
                        recipes.append(resolved_custom[recipe_id])
                        seen_recipe_ids.add(recipe_id)

            total_recipe_count += len(recipes)
            payload_days.append(
                {
                    "date": day_key,
                    "title": (
                        calendar_day.title
                        if calendar_day is not None
                        else calendar_date.strftime("%d.%m.%Y")
                    ),
                    "recipe_count": len(recipes),
                    "recipes": recipes,
                }
            )

        return {
            "requested_date": day.isoformat(),
            "week_start": week_start.isoformat(),
            "week_end": week_dates[-1].isoformat(),
            "days": payload_days,
            "summary": {
                "recipe_count": total_recipe_count,
                "populated_day_count": sum(
                    bool(payload_day["recipes"]) for payload_day in payload_days
                ),
                "api_returned_day_count": len(calendar_days),
            },
        }

    async def _get_meal_plan_day(self, day: date) -> dict[str, Any]:
        """Return one day from the normalized weekly meal-plan payload."""

        week = await self.get_meal_plan_week(day)
        return next(
            payload_day
            for payload_day in week["days"]
            if payload_day["date"] == day.isoformat()
        )

    async def add_meal_plan_recipes(
        self,
        day: date,
        recipe_ids: list[str],
        recipe_source: str = "auto",
    ) -> dict[str, Any]:
        """Add official and/or custom recipes to a Cookidoo calendar day."""

        if self._api_client is None:
            raise RuntimeError("Not connected to Cookidoo")

        unique_recipe_ids = list(
            dict.fromkeys(recipe_id.strip() for recipe_id in recipe_ids if recipe_id.strip())
        )
        if not unique_recipe_ids:
            raise ValueError("At least one recipe ID is required")

        official_ids: list[str] = []
        custom_ids: list[str] = []
        for recipe_id in unique_recipe_ids:
            source = self._meal_plan_recipe_source(recipe_id, recipe_source)
            if source == "official":
                official_ids.append(recipe_id)
            else:
                custom_ids.append(recipe_id)

        if official_ids:
            await self._api_client.add_recipes_to_calendar(day, official_ids)
        if custom_ids:
            await self._api_client.add_custom_recipes_to_calendar(day, custom_ids)

        return {
            "operation": "added",
            "date": day.isoformat(),
            "official_recipe_ids": official_ids,
            "custom_recipe_ids": custom_ids,
            "day": await self._get_meal_plan_day(day),
        }

    async def remove_meal_plan_recipe(
        self,
        day: date,
        recipe_id: str,
        recipe_source: str = "auto",
    ) -> dict[str, Any]:
        """Remove one official or custom recipe from a calendar day."""

        if self._api_client is None:
            raise RuntimeError("Not connected to Cookidoo")

        source = self._meal_plan_recipe_source(recipe_id, recipe_source)
        await self._delete_meal_plan_recipe_request(
            day,
            recipe_id,
            source,
        )

        return {
            "operation": "removed",
            "date": day.isoformat(),
            "recipe_id": recipe_id,
            "recipe_source": source,
            "day": await self._get_meal_plan_day(day),
        }

    async def _delete_meal_plan_recipe_request(
        self,
        day: date,
        recipe_id: str,
        source: str,
    ) -> None:
        """Delete a calendar entry without parsing Cookidoo's nullable content.

        cookidoo-api expects every successful DELETE to return a calendar-day
        object. Cookidoo instead returns ``content: null`` when the removed
        recipe was the day's final entry, even though the deletion succeeded.
        """

        if self._api_client is None:
            raise RuntimeError("Not connected to Cookidoo")

        url = self._api_client.api_endpoint / (
            REMOVE_RECIPE_FROM_CALENDER_PATH.format(
                **self._api_client._cfg.localization.__dict__,
                day=day.isoformat(),
                recipe=recipe_id,
            )
        )
        params = {"recipeSource": "CUSTOMER"} if source == "custom" else None
        async with self._api_client._session.delete(
            url,
            headers=self._api_client._api_headers,
            params=params,
        ) as response:
            response_text = await response.text()
            if response.status > 299:
                raise RuntimeError(
                    "Cookidoo rejected calendar removal. "
                    f"Status: {response.status}, Error: {response_text}"
                )

    async def move_meal_plan_recipe(
        self,
        recipe_id: str,
        from_day: date,
        to_day: date,
        recipe_source: str = "auto",
    ) -> dict[str, Any]:
        """Move a recipe between calendar days with rollback on failure."""

        if from_day == to_day:
            return {
                "operation": "unchanged",
                "recipe_id": recipe_id,
                "recipe_source": self._meal_plan_recipe_source(
                    recipe_id,
                    recipe_source,
                ),
                "from_date": from_day.isoformat(),
                "to_date": to_day.isoformat(),
                "from_day": await self._get_meal_plan_day(from_day),
                "to_day": await self._get_meal_plan_day(to_day),
            }

        source = self._meal_plan_recipe_source(recipe_id, recipe_source)
        target_before = await self._get_meal_plan_day(to_day)
        already_on_target = any(
            recipe["id"] == recipe_id for recipe in target_before["recipes"]
        )
        added_to_target = False

        try:
            if not already_on_target:
                await self.add_meal_plan_recipes(
                    to_day,
                    [recipe_id],
                    source,
                )
                added_to_target = True
            await self.remove_meal_plan_recipe(
                from_day,
                recipe_id,
                source,
            )
        except Exception as error:
            if added_to_target:
                try:
                    await self.remove_meal_plan_recipe(
                        to_day,
                        recipe_id,
                        source,
                    )
                except Exception as rollback_error:
                    raise RuntimeError(
                        f"Move failed ({error}); rollback also failed "
                        f"({rollback_error})"
                    ) from error
            raise

        return {
            "operation": "moved",
            "recipe_id": recipe_id,
            "recipe_source": source,
            "from_date": from_day.isoformat(),
            "to_date": to_day.isoformat(),
            "from_day": await self._get_meal_plan_day(from_day),
            "to_day": await self._get_meal_plan_day(to_day),
        }

    async def create_custom_recipe(
        self,
        name: str,
        ingredients: list[str | RecipeIngredient],
        steps: list[str | RecipeStep],
        servings: int = 4,
        prep_time: int = 30,
        total_time: int = 60,
        hints: Optional[list[str]] = None,
    ) -> str:
        """
        Create a completely new custom recipe from scratch using the undocumented API.

        Args:
            name: Recipe name
            ingredients: List of ingredient descriptions
            steps: List of cooking step descriptions
            servings: Number of servings (default: 4)
            prep_time: Preparation time in minutes (default: 30)
            total_time: Total cooking time in minutes (default: 60)
            hints: Optional list of hints/tips for the recipe

        Returns:
            str: The created recipe ID

        Raises:
            Exception: If recipe creation fails
        """
        if not self._api_client or not self._session:
            raise Exception("Not authenticated. Please call login() first.")

        try:
            localization = self._api_client.localization
            # Extract base domain from the URL (e.g., "https://cookidoo.fr/foundation/fr-FR" -> "https://cookidoo.fr")
            url_parts = localization.url.split("/")
            base_url = f"{url_parts[0]}//{url_parts[2]}"  # protocol + domain
            locale = localization.language

            # Headers for the undocumented API
            headers = {
                **self._api_client._api_headers,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Use the API client's session to ensure cookies are shared
            api_session = self._api_client._session

            # Step 1: Create the recipe with just the name
            create_url = f"{base_url}/created-recipes/{locale}"
            create_data = {"recipeName": name}

            async with api_session.post(
                create_url, json=create_data, headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to create recipe. Status: {response.status}, Error: {error_text}"
                    )

                result = await response.json()
                recipe_id = result.get("recipeId")

                if not recipe_id:
                    raise Exception("No recipe ID returned from creation")

            # Step 2: Update recipe with ingredients
            update_url = f"{base_url}/created-recipes/{locale}/{recipe_id}"

            # PATCH requires a complete recipe structure with ALL required fields
            update_data = {
                "name": name,
                "image": None,  # Can be null or match pattern: ^((prod|nonprod)/img/customer-recipe/)?[A-Za-z0-9-_]{1,}.(bmp|jpe|jpeg|jpg|png)$
                "isImageOwnedByUser": False,
                "tools": ["TM6"],
                "yield": {"value": servings, "unitText": "portion"},
                "prepTime": prep_time * 60,  # Convert minutes to seconds
                "cookTime": 0,
                "totalTime": total_time * 60,  # Convert minutes to seconds
                "ingredients": [
                    ingredient_to_api(ingredient) for ingredient in ingredients
                ],
                "instructions": [step_to_api(step) for step in steps],
                "hints": (
                    "\n".join(hints)
                    if hints and isinstance(hints, list)
                    else (hints if hints else "")
                ),
                "workStatus": "PRIVATE",
                "recipeMetadata": {"requiresAnnotationsCheck": False},
            }

            await asyncio.sleep(5)

            async with api_session.patch(
                update_url, json=update_data, headers=headers
            ) as response:
                response_text = await response.text()

                if response.status not in [200, 204]:
                    raise Exception(f"Failed to update recipe: {response_text}")

            return recipe_id

        except Exception as e:
            raise Exception(f"Failed to create custom recipe: {str(e)}") from e

    async def update_custom_recipe_steps(
        self,
        recipe_id: str,
        steps: list[str | RecipeStep],
    ) -> None:
        """Replace a custom recipe's steps, including guided-cooking annotations."""

        await self._patch_custom_recipe(
            recipe_id,
            {"instructions": [step_to_api(step) for step in steps]},
        )

    async def update_custom_recipe_ingredients(
        self,
        recipe_id: str,
        ingredients: list[str | RecipeIngredient],
    ) -> None:
        """Replace a custom recipe's ingredients, including structured amounts."""

        await self._patch_custom_recipe(
            recipe_id,
            {
                "ingredients": [
                    ingredient_to_api(ingredient) for ingredient in ingredients
                ]
            },
        )

    async def upload_custom_recipe_image(
        self,
        recipe_id: str,
        image_path: str,
    ) -> dict[str, str]:
        """Upload a local image and attach it to a custom Cookidoo recipe.

        Cookidoo signs a Cloudinary upload first, then expects the returned
        customer-recipe image key in a normal partial recipe PATCH. Local
        images are normalized to JPEG so formats such as WebP are accepted by
        both Cloudinary and Cookidoo's recipe image validation.
        """

        if not self._api_client or not self._session:
            raise Exception("Not authenticated. Please call login() first.")

        image_bytes, content_type, filename = self._prepare_custom_recipe_image(
            image_path
        )
        timestamp = int(time.time())
        signature = await self._get_custom_recipe_image_signature(timestamp)
        uploaded = await self._upload_custom_recipe_image_to_cloudinary(
            image_bytes=image_bytes,
            content_type=content_type,
            filename=filename,
            timestamp=timestamp,
            signature=signature,
        )

        public_id = uploaded.get("public_id")
        image_format = uploaded.get("format")
        if not public_id or not image_format:
            raise Exception(
                "Cookidoo image upload response did not contain an image key."
            )

        image_key = f"{public_id}.{image_format}"
        await self._patch_custom_recipe(
            recipe_id,
            {
                "image": image_key,
                "isImageOwnedByUser": True,
            },
        )
        return {
            "recipe_id": recipe_id,
            "image": image_key,
            "secure_url": str(uploaded.get("secure_url") or ""),
            "filename": filename,
        }

    @staticmethod
    def _prepare_custom_recipe_image(
        image_path: str,
    ) -> tuple[bytes, str, str]:
        """Read and normalize a local recipe image to an uploadable JPEG."""

        path = Path(image_path).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"Image file does not exist: {path}")
        if path.stat().st_size > MAX_CUSTOM_RECIPE_IMAGE_BYTES:
            raise ValueError("Recipe image must be 10 MB or smaller.")

        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source)
                if "A" in image.getbands():
                    background = Image.new("RGB", image.size, "white")
                    alpha = image.getchannel("A")
                    background.paste(image, mask=alpha)
                    image = background
                else:
                    image = image.convert("RGB")

                output = BytesIO()
                image.save(output, format="JPEG", quality=90, optimize=True)
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError(f"Unsupported or invalid image file: {path}") from error

        image_bytes = output.getvalue()
        if len(image_bytes) > MAX_CUSTOM_RECIPE_IMAGE_BYTES:
            raise ValueError(
                "Converted recipe image is larger than Cookidoo's 10 MB limit."
            )
        return image_bytes, "image/jpeg", f"{path.stem}.jpg"

    async def _get_custom_recipe_image_signature(self, timestamp: int) -> str:
        """Request Cookidoo's short-lived signature for a Cloudinary upload."""

        if not self._api_client:
            raise Exception("Not authenticated. Please call login() first.")

        localization = self._api_client.localization
        url_parts = localization.url.split("/")
        base_url = f"{url_parts[0]}//{url_parts[2]}"
        signature_url = (
            f"{base_url}/created-recipes/{localization.language}/image/signature"
        )
        headers = {
            **self._api_client._api_headers,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        async with self._api_client._session.post(
            signature_url,
            json={"source": "uw", "timestamp": timestamp},
            headers=headers,
        ) as response:
            response_text = await response.text()
            if response.status != 200:
                raise Exception(
                    "Failed to sign custom recipe image upload. "
                    f"Status: {response.status}, Error: {response_text}"
                )
            try:
                payload = json.loads(response_text)
            except json.JSONDecodeError as error:
                raise Exception(
                    "Cookidoo image signature response was invalid."
                ) from error

        signature = payload.get("signature")
        if not signature:
            raise Exception(
                "Cookidoo image signature response was missing a signature."
            )
        return str(signature)

    async def _upload_custom_recipe_image_to_cloudinary(
        self,
        *,
        image_bytes: bytes,
        content_type: str,
        filename: str,
        timestamp: int,
        signature: str,
    ) -> dict[str, Any]:
        """Send image bytes to Cookidoo's signed Cloudinary upload preset."""

        if not self._api_client:
            raise Exception("Not authenticated. Please call login() first.")

        form = FormData()
        form.add_field(
            "file",
            image_bytes,
            filename=filename,
            content_type=content_type,
        )
        form.add_field("api_key", CLOUDINARY_API_KEY)
        form.add_field("timestamp", str(timestamp))
        form.add_field("source", "uw")
        form.add_field("upload_preset", CLOUDINARY_UPLOAD_PRESET)
        form.add_field("signature", signature)

        async with self._api_client._session.post(
            CLOUDINARY_UPLOAD_URL,
            data=form,
        ) as response:
            response_text = await response.text()
            if response.status > 299:
                raise Exception(
                    "Cookidoo image storage rejected the upload. "
                    f"Status: {response.status}, Error: {response_text}"
                )
            try:
                payload = json.loads(response_text)
            except json.JSONDecodeError as error:
                raise Exception(
                    "Cookidoo image storage returned an invalid response."
                ) from error

        if not isinstance(payload, dict):
            raise Exception("Cookidoo image storage returned an invalid response.")
        return payload

    async def _patch_custom_recipe(
        self,
        recipe_id: str,
        update_data: dict[str, Any],
    ) -> None:
        """Apply the same partial PATCH used by Cookidoo's recipe editor."""

        if not self._api_client or not self._session:
            raise Exception("Not authenticated. Please call login() first.")

        localization = self._api_client.localization
        url_parts = localization.url.split("/")
        base_url = f"{url_parts[0]}//{url_parts[2]}"
        update_url = f"{base_url}/created-recipes/{localization.language}/{recipe_id}"
        headers = {
            **self._api_client._api_headers,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with self._api_client._session.patch(
            update_url,
            json=update_data,
            headers=headers,
        ) as response:
            response_text = await response.text()
            if response.status not in [200, 204]:
                raise Exception(
                    f"Failed to update custom recipe. "
                    f"Status: {response.status}, Error: {response_text}"
                )

    @property
    def api_client(self) -> Optional[Cookidoo]:
        """Get the current API client instance."""
        return self._api_client
