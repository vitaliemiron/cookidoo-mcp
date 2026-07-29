import pytest

from cookidoo_service import load_cookidoo_credentials


def test_load_cookidoo_credentials_reads_environment(monkeypatch) -> None:
    monkeypatch.setattr("cookidoo_service.load_dotenv", lambda: False)
    monkeypatch.setenv("COOKIDOO_EMAIL", "test@example.com")
    monkeypatch.setenv("COOKIDOO_PASSWORD", "test-password")

    assert load_cookidoo_credentials() == (
        "test@example.com",
        "test-password",
    )


def test_load_cookidoo_credentials_requires_both_values(monkeypatch) -> None:
    monkeypatch.setattr("cookidoo_service.load_dotenv", lambda: False)
    monkeypatch.delenv("COOKIDOO_EMAIL", raising=False)
    monkeypatch.delenv("COOKIDOO_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="Missing Cookidoo credentials"):
        load_cookidoo_credentials()
