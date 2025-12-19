from typing import Any


class ValidationError(Exception):
    """Validation error for single field.

    Attributes:
        field_name: Field name in schema
        env_var: Environment variable name
        message: Error description
        value: Value that failed validation (if available)
        expected_type: Expected data type (if applicable)
    """

    def __init__(
        self,
        field_name: str,
        env_var: str,
        message: str,
        value: Any | None = None,
        expected_type: str | None = None,
    ) -> None:
        """Initializes validation error.

        Args:
            field_name: Field name in schema
            env_var: Environment variable name
            message: Error description
            value: Value that failed validation
            expected_type: Expected data type
        """
        self.field_name = field_name
        self.env_var = env_var
        self.message = message
        self.value = value
        self.expected_type = expected_type
        super().__init__(message)

    def format(self) -> str:
        """Formats error into readable string.

        Returns:
            Formatted error message
        """
        msg = f"{self.env_var}: {self.message}"

        if self.expected_type:
            msg += f" (expected type: {self.expected_type})"

        if self.value is not None:
            value_repr = repr(self.value)
            if len(value_repr) > 50:
                value_repr = value_repr[:47] + "..."
            msg += f" [got: {value_repr}]"

        return msg

    def __repr__(self) -> str:
        """Returns string representation of error.

        Returns:
            String representation for debugging
        """
        return (
            f"ValidationError(field={self.field_name!r}, "
            f"env_var={self.env_var!r}, message={self.message!r})"
        )


class EnvSchemaError(Exception):
    """Exception during environment schema loading and validation.

    Aggregates multiple validation errors and formats them
    into readable message.

    Attributes:
        errors: List of validation errors
    """

    def __init__(self, errors: list[ValidationError]) -> None:
        """Initializes exception with set of errors.

        Args:
            errors: List of validation errors
        """
        self.errors = errors
        message = self._format_errors()
        super().__init__(message)

    def _format_errors(self) -> str:
        """Formats all errors into single message.

        Returns:
            Formatted message with all errors
        """
        if not self.errors:
            return "Unknown environment schema error"

        error_count = len(self.errors)
        plural = "s" if error_count > 1 else ""

        lines = [f"Failed to load environment variables ({error_count} error{plural}):"]

        for error in self.errors:
            lines.append(f"  * {error.format()}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Returns string representation of exception.

        Returns:
            String representation for debugging
        """
        return f"EnvSchemaError(errors={self.errors!r})"
