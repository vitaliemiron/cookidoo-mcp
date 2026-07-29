# Create a Thermomix guided-cooking recipe with AI

Last verified: 2026-07-29.

Write the complete human-readable recipe first, split every ingredient action
from the machine action that follows, then add validated `INGREDIENT`, `TTS`,
or `MODE` annotations. Calculate each position against the final text before
upload.

## Annotation families

- `INGREDIENT` links a phrase in the step to an ingredient description. A
  nested `VOLUME` can store amount, unit, unit text, and an optional range.
- `TTS` stores manual time, temperature, speed, and optional `CCW` reverse.
- `MODE` stores a supported Thermomix smart function with mode-specific data.

Supported mode schemas currently include `DOUGH`, `BLEND`, `TURBO`,
`WARM_UP`, `RICE_COOKER`, `STEAMING`, and `BROWNING`.

## Workflow

1. Confirm ingredients, servings, tools, times, and complete instructions.
2. Adapt the method without inventing unsupported modes or unsafe parameters.
3. Make every sentence readable to a person.
4. Separate ingredient and machine actions.
5. Add annotation data represented by the sentence.
6. Calculate JavaScript UTF-16 positions.
7. Validate the complete recipe and upload it.
8. Read the saved private recipe and verify it.

Schema validity does not guarantee culinary or food-safety quality. These are
structured private customer recipes, not official Vorwerk Guided Cooking
recipes.

Human guide:
https://vitaliemiron.github.io/cookidoo-mcp/use-cases/create-thermomix-guided-recipe/
