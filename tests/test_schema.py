import os

import pytest

from envschema import EnvSchema, Field
from envschema.errors import EnvSchemaError


class TestEnvSchema:
    """Tests for EnvSchema."""

    def test_simple_schema(self) -> None:
        """Checks simple schema with required fields."""

        class Settings(EnvSchema):
            port: int
            host: str

        env = {"PORT": "8080", "HOST": "localhost"}
        settings = Settings.load(env=env)

        assert settings.port == 8080
        assert settings.host == "localhost"

    def test_schema_with_defaults(self) -> None:
        """Checks schema with default values."""

        class Settings(EnvSchema):
            port: int = 3000
            debug: bool = False
            host: str

        env = {"HOST": "localhost"}
        settings = Settings.load(env=env)

        assert settings.port == 3000
        assert settings.debug is False
        assert settings.host == "localhost"

    def test_schema_with_field_descriptors(self) -> None:
        """Checks schema with Field descriptors."""

        class Settings(EnvSchema):
            port: int = Field(default=3000)
            api_key: str = Field(env="SECRET_API_KEY")
            debug: bool = False

        env = {"SECRET_API_KEY": "secret123"}
        settings = Settings.load(env=env)

        assert settings.port == 3000
        assert settings.api_key == "secret123"
        assert settings.debug is False

    def test_missing_required_field(self) -> None:
        """Checks error when required field is missing."""

        class Settings(EnvSchema):
            port: int
            host: str

        env = {"PORT": "8080"}

        with pytest.raises(EnvSchemaError) as exc_info:
            Settings.load(env=env)

        error = exc_info.value
        assert len(error.errors) == 1
        assert error.errors[0].field_name == "host"
        assert "missing required" in error.errors[0].message

    def test_invalid_type(self) -> None:
        """Checks error on invalid type."""

        class Settings(EnvSchema):
            port: int

        env = {"PORT": "not_a_number"}

        with pytest.raises(EnvSchemaError) as exc_info:
            Settings.load(env=env)

        error = exc_info.value
        assert len(error.errors) == 1
        assert error.errors[0].field_name == "port"

    def test_multiple_errors(self) -> None:
        """Checks multiple validation errors."""

        class Settings(EnvSchema):
            port: int
            host: str
            debug: bool

        env = {"PORT": "not_a_number", "DEBUG": "maybe"}

        with pytest.raises(EnvSchemaError) as exc_info:
            Settings.load(env=env)

        error = exc_info.value
        assert len(error.errors) >= 2

    def test_list_type(self) -> None:
        """Checks working with lists."""

        class Settings(EnvSchema):
            hosts: list[str]
            ports: list[int]

        env = {
            "HOSTS": "host1,host2,host3",
            "PORTS": "[8080, 9090, 3000]",
        }
        settings = Settings.load(env=env)

        assert settings.hosts == ["host1", "host2", "host3"]
        assert settings.ports == [8080, 9090, 3000]

    def test_prefix(self) -> None:
        """Checks working with prefix."""

        class Settings(EnvSchema):
            port: int
            host: str

        env = {"APP_PORT": "8080", "APP_HOST": "localhost"}
        settings = Settings.load(env=env, prefix="APP_")

        assert settings.port == 8080
        assert settings.host == "localhost"

    def test_custom_env_name_with_prefix(self) -> None:
        """Checks custom variable name with prefix."""

        class Settings(EnvSchema):
            api_key: str = Field(env="SECRET_KEY")

        env = {"APP_SECRET_KEY": "secret123"}
        settings = Settings.load(env=env, prefix="APP_")

        assert settings.api_key == "secret123"

    def test_load_from_os_environ(self) -> None:
        """Checks loading from os.environ."""

        class Settings(EnvSchema):
            test_var: str

        os.environ["TEST_VAR"] = "test_value"
        try:
            settings = Settings.load()
            assert settings.test_var == "test_value"
        finally:
            os.environ.pop("TEST_VAR", None)

    def test_repr(self) -> None:
        """Checks string representation of schema."""

        class Settings(EnvSchema):
            port: int
            host: str

        env = {"PORT": "8080", "HOST": "localhost"}
        settings = Settings.load(env=env)

        repr_str = repr(settings)
        assert "Settings" in repr_str
        assert "port=8080" in repr_str
        assert "host='localhost'" in repr_str

    def test_init_with_values(self) -> None:
        """Checks initialization with explicit values."""

        class Settings(EnvSchema):
            port: int
            host: str

        settings = Settings(port=8080, host="localhost")

        assert settings.port == 8080
        assert settings.host == "localhost"

    def test_bool_values(self) -> None:
        """Checks working with boolean values."""

        class Settings(EnvSchema):
            debug: bool
            enabled: bool = True

        env = {"DEBUG": "true"}
        settings = Settings.load(env=env)

        assert settings.debug is True
        assert settings.enabled is True

        env = {"DEBUG": "false", "ENABLED": "0"}
        settings = Settings.load(env=env)

        assert settings.debug is False
        assert settings.enabled is False

    def test_float_values(self) -> None:
        """Checks working with float values."""

        class Settings(EnvSchema):
            ratio: float
            price: float = 99.99

        env = {"RATIO": "3.14"}
        settings = Settings.load(env=env)

        assert settings.ratio == 3.14
        assert settings.price == 99.99

    def test_dict_type(self) -> None:
        """Checks working with dictionaries."""

        class Settings(EnvSchema):
            config: dict

        env = {"CONFIG": '{"key": "value", "num": 42}'}
        settings = Settings.load(env=env)

        assert settings.config == {"key": "value", "num": 42}
