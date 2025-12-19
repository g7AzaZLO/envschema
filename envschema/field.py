from typing import Any

_MISSING = object()


class Field:
    """Descriptor for environment schema field description.

    Attributes:
        default: Default value (if not required)
        env: Custom environment variable name
        description: Field description for documentation
        prefix: Prefix for nested structures
    """

    def __init__(
        self,
        default: Any = _MISSING,
        env: str | None = None,
        description: str | None = None,
        prefix: str | None = None,
    ) -> None:
        """Initializes field descriptor.

        Args:
            default: Default value. If not specified, field is required
            env: Custom environment variable name
            description: Field description for auto-generated documentation
            prefix: Prefix for nested structures (e.g., "DB_")
        """
        self.default = default
        self.env = env
        self.description = description
        self.prefix = prefix
        self._name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when descriptor is defined in class.

        Args:
            owner: Owner class
            name: Attribute name in class
        """
        self._name = name

    @property
    def name(self) -> str:
        """Returns field name.

        Returns:
            Field name in schema

        Raises:
            RuntimeError: If descriptor was not properly initialized
        """
        if self._name is None:
            raise RuntimeError(
                "Field descriptor was not properly initialized. "
                "Make sure it's used as a class attribute."
            )
        return self._name

    def get_env_name(self, prefix: str = "") -> str:
        """Gets environment variable name for field.

        Applies prefix (if any) and converts to UPPER_CASE.

        Args:
            prefix: Schema prefix (if field is in nested structure)

        Returns:
            Environment variable name (UPPER_CASE)
        """
        if self.env:
            if prefix:
                return f"{prefix}{self.env}"
            return self.env

        env_name = self.name.upper()

        if self.prefix:
            env_name = f"{self.prefix}{env_name}"

        if prefix:
            env_name = f"{prefix}{env_name}"

        return env_name

    def has_default(self) -> bool:
        """Checks if field has default value.

        Returns:
            True if field has default value, False if required
        """
        return self.default is not _MISSING

    def get_default(self) -> Any:
        """Gets default value.

        Returns:
            Default value

        Raises:
            RuntimeError: If field has no default value
        """
        if not self.has_default():
            field_name = self._name or "<unnamed>"
            raise RuntimeError(f"Field '{field_name}' has no default value")
        return self.default

    def __repr__(self) -> str:
        """Returns string representation of descriptor.

        Returns:
            String representation for debugging
        """
        parts = []

        if self.has_default():
            parts.append(f"default={self.default!r}")

        if self.env:
            parts.append(f"env={self.env!r}")

        if self.description:
            parts.append(f"description={self.description!r}")

        if self.prefix:
            parts.append(f"prefix={self.prefix!r}")

        args = ", ".join(parts) if parts else ""
        return f"Field({args})"


def field_from_default(default_value: Any) -> Field:
    """Creates Field from default value.

    Used for automatic Field creation from simple defaults.

    Args:
        default_value: Default value

    Returns:
        Field with specified default value

    Example:
        >>> class Settings(EnvSchema):
        ...     debug: bool = False  # Automatically → Field(default=False)
    """
    return Field(default=default_value)
