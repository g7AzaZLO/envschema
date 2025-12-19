from envschema.errors import EnvSchemaError, ValidationError


class TestValidationError:
    """Tests for ValidationError."""

    def test_initialization(self) -> None:
        """Checks validation error initialization."""
        error = ValidationError(
            field_name="port",
            env_var="PORT",
            message="invalid value",
            value="abc",
            expected_type="int",
        )

        assert error.field_name == "port"
        assert error.env_var == "PORT"
        assert error.message == "invalid value"
        assert error.value == "abc"
        assert error.expected_type == "int"
        assert str(error) == "invalid value"

    def test_format(self) -> None:
        """Checks error formatting."""
        error = ValidationError(
            field_name="port",
            env_var="PORT",
            message="invalid value",
            value="abc",
            expected_type="int",
        )

        formatted = error.format()
        assert "PORT" in formatted
        assert "invalid value" in formatted
        assert "int" in formatted
        assert "abc" in formatted

    def test_format_without_value(self) -> None:
        """Checks formatting without value."""
        error = ValidationError(
            field_name="port",
            env_var="PORT",
            message="missing required",
            expected_type="int",
        )

        formatted = error.format()
        assert "PORT" in formatted
        assert "missing required" in formatted
        assert "abc" not in formatted

    def test_repr(self) -> None:
        """Checks string representation."""
        error = ValidationError(
            field_name="port",
            env_var="PORT",
            message="invalid value",
        )

        repr_str = repr(error)
        assert "ValidationError" in repr_str
        assert "port" in repr_str
        assert "PORT" in repr_str


class TestEnvSchemaError:
    """Tests for EnvSchemaError."""

    def test_single_error(self) -> None:
        """Checks exception with single error."""
        validation_error = ValidationError(
            field_name="port",
            env_var="PORT",
            message="missing required",
        )

        error = EnvSchemaError([validation_error])
        assert len(error.errors) == 1
        assert error.errors[0] == validation_error

        message = str(error)
        assert "1 error" in message
        assert "PORT" in message

    def test_multiple_errors(self) -> None:
        """Checks exception with multiple errors."""
        error1 = ValidationError(
            field_name="port",
            env_var="PORT",
            message="missing required",
        )
        error2 = ValidationError(
            field_name="host",
            env_var="HOST",
            message="invalid format",
        )

        error = EnvSchemaError([error1, error2])
        assert len(error.errors) == 2

        message = str(error)
        assert "2 errors" in message
        assert "PORT" in message
        assert "HOST" in message

    def test_empty_errors(self) -> None:
        """Checks exception without errors."""
        error = EnvSchemaError([])
        assert len(error.errors) == 0
        assert "Unknown environment schema error" in str(error)

    def test_repr(self) -> None:
        """Checks string representation."""
        validation_error = ValidationError(
            field_name="port",
            env_var="PORT",
            message="missing required",
        )

        error = EnvSchemaError([validation_error])
        repr_str = repr(error)
        assert "EnvSchemaError" in repr_str
