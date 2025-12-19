import pytest

from envschema.field import Field, field_from_default


class TestField:
    """Tests for Field descriptor."""

    def test_initialization_with_default(self) -> None:
        """Checks initialization with default value."""
        field = Field(default=42)
        assert field.has_default() is True
        assert field.get_default() == 42

    def test_initialization_without_default(self) -> None:
        """Checks initialization without default value."""
        field = Field()
        assert field.has_default() is False

        with pytest.raises(RuntimeError, match="has no default value"):
            field.get_default()

    def test_set_name(self) -> None:
        """Checks setting field name."""
        field = Field()

        class TestClass:
            test_field = field

        assert field.name == "test_field"

    def test_name_before_set_name(self) -> None:
        """Checks error when accessing name before set_name."""
        field = Field()
        with pytest.raises(
            RuntimeError, match="Field descriptor was not properly initialized"
        ):
            _ = field.name

    def test_get_env_name_default(self) -> None:
        """Checks getting default environment variable name."""
        field = Field()

        class TestClass:
            my_field = field

        assert field.get_env_name() == "MY_FIELD"

    def test_get_env_name_custom(self) -> None:
        """Checks getting custom environment variable name."""
        field = Field(env="CUSTOM_NAME")

        class TestClass:
            my_field = field

        assert field.get_env_name() == "CUSTOM_NAME"

    def test_get_env_name_with_prefix(self) -> None:
        """Checks getting name with schema prefix."""
        field = Field()

        class TestClass:
            my_field = field

        assert field.get_env_name(prefix="APP_") == "APP_MY_FIELD"

    def test_get_env_name_with_field_prefix(self) -> None:
        """Checks getting name with field prefix."""
        field = Field(prefix="DB_")

        class TestClass:
            my_field = field

        assert field.get_env_name() == "DB_MY_FIELD"

    def test_get_env_name_with_both_prefixes(self) -> None:
        """Checks getting name with both prefixes."""
        field = Field(prefix="DB_")

        class TestClass:
            my_field = field

        assert field.get_env_name(prefix="APP_") == "APP_DB_MY_FIELD"

    def test_repr_with_default(self) -> None:
        """Checks string representation with default."""
        field = Field(default=42)
        repr_str = repr(field)
        assert "default=42" in repr_str

    def test_repr_with_env(self) -> None:
        """Checks string representation with env."""
        field = Field(env="CUSTOM_NAME")
        repr_str = repr(field)
        assert "env='CUSTOM_NAME'" in repr_str

    def test_repr_with_description(self) -> None:
        """Checks string representation with description."""
        field = Field(description="Test field")
        repr_str = repr(field)
        assert "description='Test field'" in repr_str

    def test_repr_empty(self) -> None:
        """Checks string representation of empty Field."""
        field = Field()
        repr_str = repr(field)
        assert repr_str == "Field()"


class TestFieldFromDefault:
    """Tests for field_from_default."""

    def test_creates_field_with_default(self) -> None:
        """Checks creating Field from default value."""
        field = field_from_default(42)
        assert field.has_default() is True
        assert field.get_default() == 42

    def test_creates_field_with_string_default(self) -> None:
        """Checks creating Field with string value."""
        field = field_from_default("default_value")
        assert field.get_default() == "default_value"

    def test_creates_field_with_bool_default(self) -> None:
        """Checks creating Field with boolean value."""
        field = field_from_default(False)
        assert field.get_default() is False
