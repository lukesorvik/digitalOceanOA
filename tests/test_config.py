import os

import pytest

from app.config import get_settings


def test_blank_max_ttl_defaults(monkeypatch):
    monkeypatch.setenv("MAX_TTL_SECONDS", "")
    settings = get_settings()
    assert settings.max_ttl_seconds == 86400


def test_invalid_max_ttl_raises(monkeypatch):
    monkeypatch.setenv("MAX_TTL_SECONDS", "abc")
    with pytest.raises(ValueError, match="MAX_TTL_SECONDS must be an integer"):
        get_settings()


def test_empty_signing_secret_raises(monkeypatch):
    monkeypatch.setenv("SIGNING_SECRET", "")
    with pytest.raises(ValueError, match="SIGNING_SECRET cannot be empty"):
        get_settings()


def test_signing_secret_is_string(monkeypatch):
    monkeypatch.setenv("SIGNING_SECRET", "my-secret-string")
    settings = get_settings()
    assert isinstance(settings.signing_secret, str)
    assert settings.signing_secret == "my-secret-string"
