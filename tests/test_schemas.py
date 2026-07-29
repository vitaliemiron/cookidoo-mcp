import unittest

from pydantic import ValidationError

from schemas import (
    RecipeIngredient,
    RecipeStep,
    ingredient_to_api,
    position_for,
    step_to_api,
)


class GuidedRecipeSchemaTests(unittest.TestCase):
    def test_tts_annotation_serializes_exact_cookidoo_shape(self) -> None:
        text = "Измельчите 30 сек./100°C/обратное вращение/скорость 4."
        marker = "30 сек./100°C/обратное вращение/скорость 4"
        step = RecipeStep(
            text=text,
            annotations=[
                {
                    "type": "TTS",
                    "data": {
                        "time": 30,
                        "temperature": {"value": "100", "unit": "C"},
                        "direction": "CCW",
                        "speed": "4",
                    },
                    "position": {
                        "offset": text.index(marker),
                        "length": len(marker),
                    },
                }
            ],
        )

        self.assertEqual(
            step_to_api(step),
            {
                "type": "STEP",
                "text": text,
                "annotations": [
                    {
                        "type": "TTS",
                        "data": {
                            "speed": "4",
                            "direction": "CCW",
                            "time": 30,
                            "temperature": {"value": "100", "unit": "C"},
                        },
                        "position": {
                            "offset": text.index(marker),
                            "length": len(marker),
                        },
                    }
                ],
            },
        )

    def test_ingredient_link_can_include_scale_amount(self) -> None:
        text = "Добавьте 75 г сахара в чашу."
        marker = "75 г сахара"
        step = RecipeStep(
            text=text,
            annotations=[
                {
                    "type": "INGREDIENT",
                    "data": {
                        "description": {
                            "text": marker,
                            "annotations": [
                                {
                                    "type": "VOLUME",
                                    "data": {
                                        "amount": 75,
                                        "unit": "gram",
                                        "unitText": "г",
                                    },
                                    "position": {"offset": 0, "length": 4},
                                }
                            ],
                        }
                    },
                    "position": {
                        "offset": text.index(marker),
                        "length": len(marker),
                    },
                }
            ],
        )

        payload = step_to_api(step)
        annotation = payload["annotations"][0]
        self.assertEqual(annotation["type"], "INGREDIENT")
        self.assertEqual(
            annotation["data"]["description"]["annotations"][0]["type"],
            "VOLUME",
        )

    def test_ingredient_and_machine_actions_must_be_separate_steps(self) -> None:
        text = "Добавьте 75 г сахара и измельчите 30 сек./скорость 4."
        ingredient_marker = "75 г сахара"
        settings_marker = "30 сек./скорость 4"

        with self.assertRaisesRegex(
            ValidationError,
            "ingredient weighing/adding must be a separate step",
        ):
            RecipeStep(
                text=text,
                annotations=[
                    {
                        "type": "INGREDIENT",
                        "data": {"description": ingredient_marker},
                        "position": position_for(
                            text,
                            ingredient_marker,
                        ).model_dump(),
                    },
                    {
                        "type": "TTS",
                        "data": {"time": 30, "speed": "4"},
                        "position": position_for(
                            text,
                            settings_marker,
                        ).model_dump(),
                    },
                ],
            )

    def test_separate_ingredient_and_machine_steps_are_valid(self) -> None:
        ingredient_text = "Добавьте 75 г сахара."
        machine_text = "Измельчите 30 сек./скорость 4."

        ingredient_step = RecipeStep(
            text=ingredient_text,
            annotations=[
                {
                    "type": "INGREDIENT",
                    "data": {"description": "75 г сахара"},
                    "position": position_for(
                        ingredient_text,
                        "75 г сахара",
                    ).model_dump(),
                }
            ],
        )
        machine_step = RecipeStep(
            text=machine_text,
            annotations=[
                {
                    "type": "TTS",
                    "data": {"time": 30, "speed": "4"},
                    "position": position_for(
                        machine_text,
                        "30 сек./скорость 4",
                    ).model_dump(),
                }
            ],
        )

        self.assertEqual(ingredient_step.annotations[0].type, "INGREDIENT")
        self.assertEqual(machine_step.annotations[0].type, "TTS")

    def test_smart_mode_payload_supports_steaming(self) -> None:
        text = "Готовьте на пару 20 мин."
        marker = "20 мин."
        step = RecipeStep(
            text=text,
            annotations=[
                {
                    "type": "MODE",
                    "name": "STEAMING",
                    "data": {
                        "time": 1200,
                        "speed": "1",
                        "direction": "CW",
                        "accessory": "Varoma",
                    },
                    "position": {
                        "offset": text.index(marker),
                        "length": len(marker),
                    },
                }
            ],
        )

        annotation = step_to_api(step)["annotations"][0]
        self.assertEqual(annotation["name"], "STEAMING")
        self.assertEqual(annotation["data"]["accessory"], "Varoma")

    def test_structured_ingredient_serializes_volume(self) -> None:
        ingredient = RecipeIngredient(
            text="75 г сахара",
            annotations=[
                {
                    "type": "VOLUME",
                    "data": {"amount": 75, "unit": "gram", "unitText": "г"},
                    "position": {"offset": 0, "length": 4},
                }
            ],
        )

        self.assertEqual(
            ingredient_to_api(ingredient)["annotations"][0]["data"]["amount"],
            75,
        )

    def test_out_of_bounds_annotation_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            RecipeStep(
                text="Mix.",
                annotations=[
                    {
                        "type": "TTS",
                        "data": {"time": 30, "speed": "4"},
                        "position": {"offset": 2, "length": 20},
                    }
                ],
            )

    def test_position_uses_javascript_utf16_offsets(self) -> None:
        text = "Смешайте 🔄 30 сек./скорость 4."
        position = position_for(text, "30 сек./скорость 4")

        self.assertEqual(position.offset, 12)
        self.assertEqual(position.length, 18)

        step = RecipeStep(
            text=text,
            annotations=[
                {
                    "type": "TTS",
                    "data": {"time": 30, "speed": "4"},
                    "position": position.model_dump(),
                }
            ],
        )
        self.assertEqual(step.annotations[0].position, position)


if __name__ == "__main__":
    unittest.main()
