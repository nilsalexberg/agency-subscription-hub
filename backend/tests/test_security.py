import pytest

from app.core.security import hash_password, verify_password


def test_hash_password_result():
    result = hash_password("secret")
    assert isinstance(result, str)
    assert result != "secret"
    assert result.startswith("$2b$")


def test_hash_password_unique_per_call():
    h1 = hash_password("secret")
    h2 = hash_password("secret")
    assert h1 != h2


def test_verify_password():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrong", hashed) is False
    assert verify_password("", hashed) is False


def test_verify_password_roundtrip_different_passwords():
    h1 = hash_password("alpha")
    h2 = hash_password("beta")
    assert verify_password("alpha", h1) is True
    assert verify_password("beta", h2) is True
    assert verify_password("alpha", h2) is False
    assert verify_password("beta", h1) is False
