import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from cookidoo_service import (
    CookidooService,
    load_cookidoo_locale,
    normalize_cookidoo_country,
    normalize_cookidoo_language,
    resolve_cookidoo_localization,
)


def test_locale_defaults_to_ro_and_en(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COOKIDOO_COUNTRY", raising=False)
    monkeypatch.delenv("COOKIDOO_LANGUAGE", raising=False)

    assert load_cookidoo_locale() == ("ro", "en")


def test_locale_uses_environment_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COOKIDOO_COUNTRY", "US")
    monkeypatch.setenv("COOKIDOO_LANGUAGE", "en_us")

    service = CookidooService("person@example.com", "secret")

    assert (service.country, service.language) == ("us", "en-US")


def test_explicit_locale_takes_precedence_over_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COOKIDOO_COUNTRY", "us")
    monkeypatch.setenv("COOKIDOO_LANGUAGE", "en-US")

    service = CookidooService(
        "person@example.com",
        "secret",
        country="DE",
        language="de_de",
    )

    assert (service.country, service.language) == ("de", "de-DE")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" RO ", "ro"),
        ("US", "us"),
    ],
)
def test_country_normalization(value: str, expected: str) -> None:
    assert normalize_cookidoo_country(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" EN ", "en"),
        ("pt_br", "pt-BR"),
        ("ZH-hans", "zh-Hans"),
        ("es-419", "es-419"),
    ],
)
def test_language_normalization(value: str, expected: str) -> None:
    assert normalize_cookidoo_language(value) == expected


@pytest.mark.parametrize("value", ["", "rom", "r0", "romania"])
def test_invalid_country_has_clear_error(value: str) -> None:
    with pytest.raises(ValueError, match="COOKIDOO_COUNTRY"):
        normalize_cookidoo_country(value)


@pytest.mark.parametrize("value", ["", "english", "en-UnitedStates", "e"])
def test_invalid_language_has_clear_error(value: str) -> None:
    with pytest.raises(ValueError, match="COOKIDOO_LANGUAGE"):
        normalize_cookidoo_language(value)


def test_valid_locale_pair_is_resolved_offline() -> None:
    expected = SimpleNamespace(
        country_code="us",
        language="en-US",
        url="https://example.test/foundation/en-US",
    )

    async def run() -> None:
        with patch(
            "cookidoo_service.get_localization_options",
            new=AsyncMock(return_value=[expected]),
        ) as localization_options:
            result = await resolve_cookidoo_localization("us", "en-US")

        assert result is expected
        localization_options.assert_awaited_once_with(
            country="us",
            language="en-US",
        )

    asyncio.run(run())


def test_invalid_language_lists_supported_values_without_credentials() -> None:
    supported = [
        SimpleNamespace(language="en"),
        SimpleNamespace(language="ro"),
    ]
    password = "password-that-must-never-appear"

    async def run() -> None:
        lookup = AsyncMock(side_effect=[[], supported])
        with patch("cookidoo_service.get_localization_options", new=lookup):
            with pytest.raises(ValueError) as error:
                await resolve_cookidoo_localization("ro", "en-US")

        message = str(error.value)
        assert "Supported languages for 'ro': en, ro" in message
        assert password not in message

    asyncio.run(run())


def test_invalid_country_has_clear_error_without_credentials() -> None:
    password = "password-that-must-never-appear"

    async def run() -> None:
        lookup = AsyncMock(side_effect=[[], []])
        with patch("cookidoo_service.get_localization_options", new=lookup):
            with pytest.raises(ValueError) as error:
                await resolve_cookidoo_localization("zz", "en")

        message = str(error.value)
        assert "does not support country 'zz'" in message
        assert password not in message

    asyncio.run(run())


def test_authentication_error_does_not_expose_password() -> None:
    password = "password-that-must-never-appear"
    localization = SimpleNamespace(
        country_code="ro",
        language="en",
        url="https://example.test/foundation/en",
    )

    async def run() -> None:
        service = CookidooService(
            "person@example.com",
            password,
            country="ro",
            language="en",
        )
        fake_client = SimpleNamespace(
            login=AsyncMock(
                side_effect=RuntimeError(f"upstream echoed {password}")
            )
        )
        fake_session = SimpleNamespace(close=AsyncMock())

        with (
            patch(
                "cookidoo_service.resolve_cookidoo_localization",
                new=AsyncMock(return_value=localization),
            ),
            patch(
                "cookidoo_service.ClientSession",
                return_value=fake_session,
            ),
            patch("cookidoo_service.Cookidoo", return_value=fake_client),
        ):
            with pytest.raises(RuntimeError) as error:
                await service.login()

        assert password not in str(error.value)
        fake_session.close.assert_awaited_once()

    asyncio.run(run())
