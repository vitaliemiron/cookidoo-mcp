# Guided cooking

Cookidoo guided actions are structured annotations attached to human-readable step text.

## Required separation

Ingredient handling and machine actions must be separate:

1. A weighing or adding step contains only `INGREDIENT` annotations.
2. The following chopping, mixing, cooking, kneading, steaming, or other Thermomix step contains its `TTS` or `MODE` annotation.

Never combine `INGREDIENT` with `TTS` or `MODE` in the same step.

## UTF-16 positions

Cookidoo expects JavaScript UTF-16 offsets. Call `calculate_annotation_position`; do not use ordinary Python `len()` or `str.index()` when emoji or astral Unicode may occur.

## Annotation families

- `TTS`: time in seconds, optional temperature, speed as a string, and optional `CCW` direction.
- `INGREDIENT`: a step-text link to an ingredient description.
- `VOLUME`: structured amount, unit, unit text, and optional maximum amount.
- `MODE`: a supported Thermomix smart mode.

Current supported modes include `DOUGH`, `BLEND`, `TURBO`, `WARM_UP`, `RICE_COOKER`, `STEAMING`, and `BROWNING`.

Always validate the final payload with `validate_guided_recipe_structure` before upload.
