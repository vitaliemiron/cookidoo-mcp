import asyncio
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock

from PIL import Image

from cookidoo_service import CookidooService


class CustomRecipeImageTests(unittest.TestCase):
    def test_prepare_custom_recipe_image_converts_webp_to_jpeg(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "recipe.webp"
            Image.new("RGBA", (32, 24), (20, 80, 120, 180)).save(
                source,
                format="WEBP",
            )

            image_bytes, content_type, filename = (
                CookidooService._prepare_custom_recipe_image(str(source))
            )

        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(filename, "recipe.jpg")
        with Image.open(BytesIO(image_bytes)) as converted:
            self.assertEqual(converted.format, "JPEG")
            self.assertEqual(converted.mode, "RGB")
            self.assertEqual(converted.size, (32, 24))

    def test_upload_custom_recipe_image_attaches_cloudinary_key(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "recipe.png"
            Image.new("RGB", (40, 30), "green").save(source, format="PNG")

            service = CookidooService("example@example.com", "secret")
            service._api_client = object()
            service._session = object()
            service._get_custom_recipe_image_signature = AsyncMock(
                return_value="signed"
            )
            service._upload_custom_recipe_image_to_cloudinary = AsyncMock(
                return_value={
                    "public_id": "prod/img/customer-recipe/recipe-id",
                    "format": "jpg",
                    "secure_url": "https://example.test/recipe.jpg",
                }
            )
            service._patch_custom_recipe = AsyncMock()

            result = asyncio.run(
                service.upload_custom_recipe_image(
                    "01TESTRECIPE",
                    str(source),
                )
            )

        self.assertEqual(
            result["image"],
            "prod/img/customer-recipe/recipe-id.jpg",
        )
        service._patch_custom_recipe.assert_awaited_once_with(
            "01TESTRECIPE",
            {
                "image": "prod/img/customer-recipe/recipe-id.jpg",
                "isImageOwnedByUser": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
