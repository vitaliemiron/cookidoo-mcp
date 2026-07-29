"""Pydantic models for Cookidoo custom recipes and guided-cooking data."""

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

COOKIDOO_SPEEDS = (
    "soft",
    "0.5",
    "1",
    "1.5",
    "2",
    "2.5",
    "3",
    "3.5",
    "4",
    "4.5",
    "5",
    "5.5",
    "6",
    "6.5",
    "7",
    "7.5",
    "8",
    "8.5",
    "9",
    "9.5",
    "10",
)


class CookidooModel(BaseModel):
    """Base model which serializes cleanly to Cookidoo request JSON."""

    model_config = ConfigDict(extra="forbid")


class AnnotationPosition(CookidooModel):
    """Character range in the surrounding ingredient or instruction text."""

    offset: int = Field(ge=0)
    length: int = Field(gt=0)


class Temperature(CookidooModel):
    """Temperature setting used by TTS and mode annotations."""

    value: str
    unit: Literal["C", "F"]


class VolumeData(CookidooModel):
    """Structured amount recognized by Cookidoo's scale UI."""

    amount: float = Field(gt=0)
    amountMax: Optional[float] = Field(default=None, gt=0)
    unit: Optional[str] = None
    unitText: Optional[str] = None


class VolumeAnnotation(CookidooModel):
    """Amount annotation embedded in an ingredient description."""

    type: Literal["VOLUME"] = "VOLUME"
    data: VolumeData
    position: AnnotationPosition


class StructuredIngredientDescription(CookidooModel):
    """Ingredient text with a machine-readable amount."""

    text: str = Field(min_length=1)
    annotations: list[VolumeAnnotation] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_annotation_positions(self) -> "StructuredIngredientDescription":
        _validate_positions(self.text, self.annotations)
        return self


class IngredientNote(CookidooModel):
    """Cookidoo ingredient warning or handling note."""

    type: str = Field(min_length=1)


class IngredientLinkData(CookidooModel):
    """Data displayed by the scale when an instruction links an ingredient."""

    description: str | StructuredIngredientDescription
    notes: Optional[list[IngredientNote]] = None


class TTSData(CookidooModel):
    """Manual Time/Temperature/Speed settings."""

    speed: str
    direction: Optional[Literal["CW", "CCW"]] = None
    time: int = Field(gt=0, le=5940)
    temperature: Optional[Temperature] = None

    @model_validator(mode="after")
    def validate_manual_setting(self) -> "TTSData":
        if self.speed not in COOKIDOO_SPEEDS:
            raise ValueError(f"unsupported Cookidoo speed: {self.speed}")
        if self.temperature and self.speed != "soft" and float(self.speed) > 6:
            raise ValueError("Cookidoo temperatures cannot be combined with speed > 6")
        if self.temperature and self.temperature.value == "OFF":
            raise ValueError("omit temperature instead of using value 'OFF'")
        return self


class ModeData(CookidooModel):
    """Union of parameters used by Cookidoo's supported smart modes."""

    speed: Optional[str] = None
    direction: Optional[Literal["CW", "CCW"]] = None
    temperature: Optional[Temperature] = None
    time: Optional[float] = Field(default=None, gt=0)
    pulseCount: Optional[int] = Field(default=None, gt=0)
    pulseCountMax: Optional[int] = Field(default=None, gt=0)
    accessory: Optional[
        Literal["Varoma", "SimmeringBasket", "VaromaAndSimmeringBasket"]
    ] = None
    power: Optional[Literal["Gentle", "Intense"]] = None


class TTSAnnotation(CookidooModel):
    """Manual guided-cooking annotation."""

    type: Literal["TTS"] = "TTS"
    data: TTSData
    position: AnnotationPosition


class ModeAnnotation(CookidooModel):
    """Smart-function annotation such as Dough, Turbo, or Steaming."""

    type: Literal["MODE"] = "MODE"
    name: Literal[
        "DOUGH",
        "BLEND",
        "TURBO",
        "WARM_UP",
        "RICE_COOKER",
        "STEAMING",
        "BROWNING",
    ]
    data: ModeData
    position: AnnotationPosition

    @model_validator(mode="after")
    def validate_mode_data(self) -> "ModeAnnotation":
        fields = set(self.data.model_dump(exclude_none=True))
        rules: dict[str, tuple[set[str], set[str]]] = {
            "DOUGH": ({"time"}, {"time"}),
            "BLEND": ({"time", "speed"}, {"time", "speed"}),
            "TURBO": ({"time"}, {"time", "pulseCount", "pulseCountMax"}),
            "WARM_UP": (
                {"temperature", "speed"},
                {"temperature", "speed"},
            ),
            "RICE_COOKER": (set(), set()),
            "STEAMING": (
                {"time", "speed", "direction", "accessory"},
                {"time", "speed", "direction", "accessory"},
            ),
            "BROWNING": (
                {"time", "temperature", "power"},
                {"time", "temperature", "power"},
            ),
        }
        required, allowed = rules[self.name]
        missing = required - fields
        unexpected = fields - allowed
        if missing:
            raise ValueError(f"{self.name} is missing required data: {sorted(missing)}")
        if unexpected:
            raise ValueError(f"{self.name} has unsupported data: {sorted(unexpected)}")

        if self.name == "DOUGH" and self.data.time and self.data.time > 1200:
            raise ValueError("DOUGH time must be between 1 and 1200 seconds")
        if self.name == "BLEND":
            if self.data.time and not 10 <= self.data.time <= 300:
                raise ValueError("BLEND time must be between 10 and 300 seconds")
            if self.data.speed not in {"6", "6.5", "7", "7.5", "8"}:
                raise ValueError("BLEND speed must be between 6 and 8")
        if self.name == "TURBO" and self.data.time not in {0.5, 1, 2}:
            raise ValueError("TURBO time must be 0.5, 1, or 2 seconds")
        if self.name == "WARM_UP" and self.data.speed not in {"soft", "1", "2"}:
            raise ValueError("WARM_UP speed must be soft, 1, or 2")
        if self.name == "STEAMING":
            if self.data.time and self.data.time > 5940:
                raise ValueError("STEAMING time cannot exceed 5940 seconds")
            if self.data.speed not in COOKIDOO_SPEEDS:
                raise ValueError(f"unsupported Cookidoo speed: {self.data.speed}")
        if self.name == "BROWNING" and self.data.time and self.data.time > 1800:
            raise ValueError("BROWNING time cannot exceed 1800 seconds")
        return self


class IngredientLinkAnnotation(CookidooModel):
    """Instruction annotation that enables weighing an ingredient."""

    type: Literal["INGREDIENT"] = "INGREDIENT"
    data: IngredientLinkData
    position: AnnotationPosition


StepAnnotation = Annotated[
    Union[TTSAnnotation, ModeAnnotation, IngredientLinkAnnotation],
    Field(discriminator="type"),
]


class RecipeIngredient(CookidooModel):
    """Cookidoo ingredient request object."""

    type: Literal["INGREDIENT"] = "INGREDIENT"
    text: str = Field(min_length=1)
    annotations: Optional[list[VolumeAnnotation]] = None

    @model_validator(mode="after")
    def validate_annotation_positions(self) -> "RecipeIngredient":
        _validate_positions(self.text, self.annotations or [])
        return self


class RecipeStep(CookidooModel):
    """Cookidoo instruction request object with one kind of guided action."""

    type: Literal["STEP"] = "STEP"
    text: str = Field(min_length=1)
    annotations: Optional[list[StepAnnotation]] = None

    @model_validator(mode="after")
    def validate_annotation_positions(self) -> "RecipeStep":
        _validate_positions(self.text, self.annotations or [])

        annotation_types = {
            annotation.type for annotation in (self.annotations or [])
        }
        if "INGREDIENT" in annotation_types and annotation_types & {"TTS", "MODE"}:
            raise ValueError(
                "ingredient weighing/adding must be a separate step from "
                "cooking, mixing, chopping, or kneading"
            )
        return self


def _validate_positions(
    text: str,
    annotations: list[VolumeAnnotation | StepAnnotation],
) -> None:
    """Ensure every Cookidoo UTF-16 range points inside its display text."""

    for annotation in annotations:
        end = annotation.position.offset + annotation.position.length
        encoded_text = text.encode("utf-16-le")
        if end * 2 > len(encoded_text):
            raise ValueError(
                "annotation position extends past the end of its display text"
            )
        try:
            selected_text = encoded_text[
                annotation.position.offset * 2 : end * 2
            ].decode("utf-16-le")
        except UnicodeDecodeError as error:
            raise ValueError(
                "annotation position splits a UTF-16 surrogate pair"
            ) from error
        if not selected_text.strip():
            raise ValueError("annotation position must point to non-whitespace text")


def utf16_length(text: str) -> int:
    """Return the length used by Cookidoo's browser editor."""

    return len(text.encode("utf-16-le")) // 2


def position_for(text: str, marker: str, occurrence: int = 1) -> AnnotationPosition:
    """Find a marker and return its zero-based Cookidoo UTF-16 position."""

    if not marker:
        raise ValueError("annotation marker cannot be empty")
    if occurrence < 1:
        raise ValueError("occurrence must be at least 1")

    start = -1
    search_from = 0
    for _ in range(occurrence):
        start = text.find(marker, search_from)
        if start == -1:
            raise ValueError(f"annotation marker not found: {marker!r}")
        search_from = start + len(marker)

    return AnnotationPosition(
        offset=utf16_length(text[:start]),
        length=utf16_length(marker),
    )


def ingredient_to_api(
    ingredient: str | RecipeIngredient,
) -> dict:
    """Convert a validated ingredient to Cookidoo's request shape."""

    if isinstance(ingredient, str):
        return {"type": "INGREDIENT", "text": ingredient}
    return ingredient.model_dump(exclude_none=True)


def step_to_api(step: str | RecipeStep) -> dict:
    """Convert a validated step to Cookidoo's request shape."""

    if isinstance(step, str):
        return {"type": "STEP", "text": step}
    return step.model_dump(exclude_none=True)


class CustomRecipe(BaseModel):
    """Model for a custom recipe to be created on Cookidoo."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Chocolate Chip Cookies",
                "ingredients": [
                    "200g flour",
                    "100g butter",
                    "100g sugar",
                    "1 egg",
                    "100g chocolate chips",
                ],
                "steps": [
                    "Mix butter and sugar until creamy",
                    "Add egg and mix well",
                    "Add flour and chocolate chips",
                    "Bake at 180°C for 12 minutes",
                ],
                "servings": 6,
                "prep_time": 15,
                "total_time": 30,
                "hints": [
                    "Don't overmix the dough",
                    "Cookies will firm up as they cool",
                ],
            }
        },
    )

    name: str = Field(..., description="Recipe name", min_length=1, max_length=200)
    ingredients: list[str | RecipeIngredient] = Field(
        ..., description="List of ingredients with quantities", min_length=1
    )
    steps: list[str | RecipeStep] = Field(
        ..., description="List of cooking steps/instructions", min_length=1
    )
    servings: int = Field(default=4, description="Number of servings", ge=1, le=20)
    prep_time: int = Field(
        default=30, description="Preparation time in minutes", ge=1, le=1440
    )
    total_time: int = Field(
        default=60, description="Total cooking time in minutes", ge=1, le=1440
    )
    hints: Optional[list[str]] = Field(
        default=None, description="Optional cooking tips or hints"
    )
