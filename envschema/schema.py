from pathlib import Path
from typing import Any, get_type_hints

from .casters import _get_type_name, cast_value, is_optional_type
from .errors import EnvSchemaError, ValidationError
from .field import _MISSING, Field, field_from_default
from .loader import load_env_with_dotenv


class EnvSchemaMeta(type):
    """Metaclass for EnvSchema.

    Processes type annotations and creates Field descriptors.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        """Creates new schema class.

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace
            **kwargs: Additional arguments

        Returns:
            New schema class
        """
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if name == "EnvSchema":
            return cls

        annotations = namespace.get("__annotations__", {})

        for field_name, _field_type in annotations.items():
            field_value = namespace.get(field_name, _MISSING)

            if isinstance(field_value, Field):
                field_value.__set_name__(cls, field_name)
            elif field_value is not _MISSING:
                field_obj = field_from_default(field_value)
                field_obj.__set_name__(cls, field_name)
                setattr(cls, field_name, field_obj)
            else:
                field_obj = Field()
                field_obj.__set_name__(cls, field_name)
                setattr(cls, field_name, field_obj)

        return cls


class EnvSchema(metaclass=EnvSchemaMeta):
    """Base class for environment variable schemas.

    Usage example:
        >>> class Settings(EnvSchema):
        ...     port: int
        ...     debug: bool = False
        ...     api_key: str = Field(env="SECRET_API_KEY")
        >>> settings = Settings.load()
    """

    def __init__(self, **values: Any) -> None:
        """Initializes schema instance with values.

        Args:
            **values: Field values
        """
        for key, value in values.items():
            setattr(self, key, value)

    @classmethod
    def _get_fields(cls) -> dict[str, tuple[Field, type]]:
        """Gets all schema fields with their types.

        Returns:
            Dictionary {field_name: (Field, type)}
        """
        fields = {}
        type_hints = get_type_hints(cls)

        for attr_name in dir(cls):
            attr_value = getattr(cls, attr_name)

            if isinstance(attr_value, Field):
                field_type = type_hints.get(attr_name, str)
                fields[attr_name] = (attr_value, field_type)

        return fields

    @classmethod
    def _is_nested_schema(cls, field_type: type) -> bool:
        """Checks if type is nested schema.

        Args:
            field_type: Field type

        Returns:
            True if type is subclass of EnvSchema
        """
        try:
            return isinstance(field_type, type) and issubclass(field_type, EnvSchema)
        except TypeError:
            return False

    @classmethod
    def load(
        cls,
        env: dict[str, str] | None = None,
        prefix: str = "",
        dotenv_path: str | Path | bool | None = None,
        dotenv_override: bool = False,
    ) -> "EnvSchema":
        """Loads and validates schema from environment variables.

        Args:
            env: Dictionary of environment variables (default: os.environ)
            prefix: Prefix for all schema variables
            dotenv_path: Path to .env file, True for auto-search, None to ignore
            dotenv_override: If True, .env overrides system variables

        Raises:
            EnvSchemaError: If validation failed
            ImportError: If python-dotenv is not installed (if using dotenv_path)
            FileNotFoundError: If .env file not found

        Example:
            >>> settings = Settings.load()  # Only os.environ
            >>> settings = Settings.load(dotenv_path=".env")  # With .env file
            >>> settings = Settings.load(dotenv_path=True)  # Auto-search .env
        """
        if env is None:
            env = load_env_with_dotenv(dotenv_path, dotenv_override)

        fields = cls._get_fields()
        errors: list[ValidationError] = []
        values: dict[str, Any] = {}

        for field_name, (field, field_type) in fields.items():
            try:
                value = cls._load_field(
                    field=field,
                    field_name=field_name,
                    field_type=field_type,
                    parent_prefix=prefix,
                    env=env,
                )
                values[field_name] = value

            except ValidationError as e:
                errors.append(e)
            except EnvSchemaError as e:
                errors.extend(e.errors)

        if errors:
            raise EnvSchemaError(errors)

        return cls(**values)

    @classmethod
    def _compute_nested_prefix(
        cls, field: Field, field_name: str, parent_prefix: str
    ) -> str:
        """Computes prefix for nested schema.

        Args:
            field: Field descriptor
            field_name: Field name in schema
            parent_prefix: Parent schema prefix

        Returns:
            Full prefix for nested schema
        """
        if field.prefix is not None:
            nested_prefix = field.prefix
        else:
            nested_prefix = f"{field_name.upper()}_"

        if parent_prefix:
            return f"{parent_prefix}{nested_prefix}"

        return nested_prefix

    @classmethod
    def _load_field(
        cls,
        field: Field,
        field_name: str,
        field_type: type,
        parent_prefix: str,
        env: dict[str, str],
    ) -> Any:
        """Loads and validates single field.

        Args:
            field: Field descriptor
            field_name: Field name in schema
            field_type: Field type
            parent_prefix: Parent schema prefix
            env: Dictionary of environment variables

        Returns:
            Field value

        Raises:
            ValidationError: If validation failed
            EnvSchemaError: If nested schema validation failed
        """
        if cls._is_nested_schema(field_type):
            return cls._load_nested_schema(
                field=field,
                field_name=field_name,
                schema_type=field_type,
                parent_prefix=parent_prefix,
                env=env,
            )

        env_name = field.get_env_name(parent_prefix)
        raw_value = env.get(env_name)

        if raw_value is None:
            if field.has_default():
                return field.get_default()
            elif is_optional_type(field_type):
                return None
            else:
                raise ValidationError(
                    field_name=field_name,
                    env_var=env_name,
                    message="missing required environment variable",
                    expected_type=_get_type_name(field_type),
                )

        try:
            return cast_value(raw_value, field_type)
        except ValueError as e:
            raise ValidationError(
                field_name=field_name,
                env_var=env_name,
                message=str(e),
                value=raw_value,
                expected_type=_get_type_name(field_type),
            ) from e

    @classmethod
    def _load_nested_schema(
        cls,
        field: Field,
        field_name: str,
        schema_type: type["EnvSchema"],
        parent_prefix: str,
        env: dict[str, str],
    ) -> "EnvSchema":
        """Loads nested schema.

        Args:
            field: Field descriptor
            field_name: Field name in schema
            schema_type: Nested schema type
            parent_prefix: Parent schema prefix
            env: Dictionary of environment variables

        Returns:
            Nested schema instance

        Raises:
            EnvSchemaError: If nested schema validation failed
        """
        nested_prefix = cls._compute_nested_prefix(field, field_name, parent_prefix)

        return schema_type.load(env=env, prefix=nested_prefix)

    def __repr__(self) -> str:
        """Returns string representation of schema.

        Returns:
            String representation for debugging
        """
        fields = self._get_fields()
        field_values = []

        for field_name in fields.keys():
            value = getattr(self, field_name, None)
            field_values.append(f"{field_name}={value!r}")

        fields_str = ", ".join(field_values)
        return f"{self.__class__.__name__}({fields_str})"
