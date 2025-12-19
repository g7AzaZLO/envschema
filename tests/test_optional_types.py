"""Tests for Optional types support."""

from typing import Optional, Union

import pytest

from envschema import EnvSchema, EnvSchemaError, Field
from envschema.casters import (
    get_optional_inner_type,
    is_optional_type,
)


def test_is_optional_type() -> None:
    """Test Optional types detection."""
    assert is_optional_type(Optional[str]) is True  # noqa: UP045
    assert is_optional_type(Union[str, None]) is True  # noqa: UP007
    assert is_optional_type(str | None) is True

    assert is_optional_type(str) is False
    assert is_optional_type(int) is False
    assert is_optional_type(Union[str, int]) is False  # noqa: UP007


def test_get_optional_inner_type() -> None:
    """Test extracting inner type from Optional."""
    assert get_optional_inner_type(Optional[str]) is str  # noqa: UP045
    assert get_optional_inner_type(Union[int, None]) is int  # noqa: UP007
    assert get_optional_inner_type(str | None) is str

    with pytest.raises(ValueError, match="not Optional"):
        get_optional_inner_type(str)


def test_optional_field_missing() -> None:
    """Test missing Optional field."""

    class Settings(EnvSchema):
        required_field: str
        optional_field: str | None

    env = {"REQUIRED_FIELD": "value"}

    settings = Settings.load(env=env)

    assert settings.required_field == "value"
    assert settings.optional_field is None


def test_optional_field_present() -> None:
    """Test Optional field with value."""

    class Settings(EnvSchema):
        optional_field: str | None

    env = {"OPTIONAL_FIELD": "present"}

    settings = Settings.load(env=env)

    assert settings.optional_field == "present"


def test_optional_int() -> None:
    """Test Optional[int]."""

    class Settings(EnvSchema):
        port: int | None

    settings1 = Settings.load(env={"PORT": "8080"})
    assert settings1.port == 8080

    settings2 = Settings.load(env={})
    assert settings2.port is None


def test_optional_bool() -> None:
    """Test Optional[bool]."""

    class Settings(EnvSchema):
        debug: bool | None

    settings1 = Settings.load(env={"DEBUG": "true"})
    assert settings1.debug is True

    settings2 = Settings.load(env={})
    assert settings2.debug is None


def test_optional_float() -> None:
    """Test Optional[float]."""

    class Settings(EnvSchema):
        threshold: float | None

    settings1 = Settings.load(env={"THRESHOLD": "0.95"})
    assert settings1.threshold == 0.95

    settings2 = Settings.load(env={})
    assert settings2.threshold is None


def test_optional_with_default() -> None:
    """Test Optional field with explicit default."""

    class Settings(EnvSchema):
        api_key: str | None = None
        timeout: int | None = 30

    settings1 = Settings.load(env={})
    assert settings1.api_key is None
    assert settings1.timeout == 30

    settings2 = Settings.load(env={"API_KEY": "secret", "TIMEOUT": "60"})
    assert settings2.api_key == "secret"
    assert settings2.timeout == 60


def test_optional_vs_required() -> None:
    """Test difference between Optional and required fields."""

    class Settings(EnvSchema):
        required: str
        optional: str | None

    with pytest.raises(EnvSchemaError) as exc_info:
        Settings.load(env={})

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0].env_var == "REQUIRED"

    settings = Settings.load(env={"REQUIRED": "value"})
    assert settings.required == "value"
    assert settings.optional is None


def test_optional_field_descriptor() -> None:
    """Test Optional with Field descriptor."""

    class Settings(EnvSchema):
        api_key: str | None = Field(description="API key")
        timeout: int | None = Field(default=30, description="Request timeout")

    settings1 = Settings.load(env={})
    assert settings1.api_key is None
    assert settings1.timeout == 30

    settings2 = Settings.load(env={"API_KEY": "secret", "TIMEOUT": "60"})
    assert settings2.api_key == "secret"
    assert settings2.timeout == 60


def test_union_syntax() -> None:
    """Test Union[T, None] syntax."""

    class Settings(EnvSchema):
        field1: str | None
        field2: str | None

    env = {}

    settings = Settings.load(env=env)

    assert settings.field1 is None
    assert settings.field2 is None


def test_optional_invalid_value() -> None:
    """Test invalid value for Optional field."""

    class Settings(EnvSchema):
        port: int | None

    env = {"PORT": "not_a_number"}

    with pytest.raises(EnvSchemaError) as exc_info:
        Settings.load(env=env)

    assert len(exc_info.value.errors) == 1
    assert "cannot cast" in exc_info.value.errors[0].message


def test_multiple_optional_fields() -> None:
    """Test multiple Optional fields."""

    class Settings(EnvSchema):
        database_url: str
        redis_url: str | None
        cache_ttl: int | None
        debug: bool | None

    env = {
        "DATABASE_URL": "postgres://localhost/db",
        "CACHE_TTL": "3600",
    }

    settings = Settings.load(env=env)

    assert settings.database_url == "postgres://localhost/db"
    assert settings.redis_url is None
    assert settings.cache_ttl == 3600
    assert settings.debug is None


def test_optional_custom_env_name() -> None:
    """Test Optional with custom variable name."""

    class Settings(EnvSchema):
        api_key: str | None = Field(env="SECRET_KEY")

    settings1 = Settings.load(env={})
    assert settings1.api_key is None

    settings2 = Settings.load(env={"SECRET_KEY": "secret123"})
    assert settings2.api_key == "secret123"


def test_optional_with_prefix() -> None:
    """Test Optional fields with prefix."""

    class Settings(EnvSchema):
        api_key: str | None
        timeout: int | None

    env = {"PROD_API_KEY": "prod_secret", "PROD_TIMEOUT": "60"}

    settings = Settings.load(env=env, prefix="PROD_")

    assert settings.api_key == "prod_secret"
    assert settings.timeout == 60


def test_optional_repr() -> None:
    """Test string representation with Optional fields."""

    class Settings(EnvSchema):
        required: str
        optional: str | None

    settings = Settings.load(env={"REQUIRED": "value"})

    repr_str = repr(settings)
    assert "required='value'" in repr_str
    assert "optional=None" in repr_str


def test_optional_mixed_with_defaults() -> None:
    """Test mixed Optional fields and defaults."""

    class Settings(EnvSchema):
        app_name: str

        debug: bool = False

        api_key: str | None

        cache_url: str | None = None

        timeout: int | None = 30

    env = {"APP_NAME": "MyApp"}

    settings = Settings.load(env=env)

    assert settings.app_name == "MyApp"
    assert settings.debug is False
    assert settings.api_key is None
    assert settings.cache_url is None
    assert settings.timeout == 30


def test_optional_in_nested_schema() -> None:
    """Test Optional fields in nested schemas."""

    class DatabaseSettings(EnvSchema):
        host: str
        port: int = 5432
        password: str | None

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")

    env = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
    }

    settings = Settings.load(env=env)

    assert settings.db.host == "localhost"
    assert settings.db.port == 5432
    assert settings.db.password is None


def test_optional_list() -> None:
    """Test Optional[list[T]]."""

    class Settings(EnvSchema):
        tags: list[str] | None
        ports: list[int] | None

    settings1 = Settings.load(env={})
    assert settings1.tags is None
    assert settings1.ports is None

    settings2 = Settings.load(
        env={"TAGS": "tag1,tag2,tag3", "PORTS": "[8080, 8081, 8082]"}
    )
    assert settings2.tags == ["tag1", "tag2", "tag3"]
    assert settings2.ports == [8080, 8081, 8082]


def test_optional_dict() -> None:
    """Test Optional[dict]."""

    class Settings(EnvSchema):
        metadata: dict | None

    settings1 = Settings.load(env={})
    assert settings1.metadata is None

    settings2 = Settings.load(env={"METADATA": '{"key": "value", "count": 42}'})
    assert settings2.metadata == {"key": "value", "count": 42}


def test_optional_empty_string() -> None:
    """Test handling empty string for Optional fields."""

    class Settings(EnvSchema):
        optional_str: str | None

    settings = Settings.load(env={"OPTIONAL_STR": ""})
    assert settings.optional_str == ""


def test_optional_semantic_difference() -> None:
    """Test semantic difference between Optional and default."""

    class Settings(EnvSchema):
        api_key: str | None

        timeout: int = 30

    env = {}

    settings = Settings.load(env=env)

    assert settings.api_key is None

    assert settings.timeout == 30
