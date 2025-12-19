import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, get_args, get_origin

from .casters import get_optional_inner_type, is_optional_type

if TYPE_CHECKING:
    from .schema import EnvSchema


class TypeHandler:
    """Handler for specific data type.

    Attributes:
        format_default: Function for formatting default value
        get_example: Function for generating example value
        type_name: Type name for documentation
    """

    def __init__(
        self,
        format_default: Callable[[Any], str],
        get_example: Callable[[], str],
        type_name: str | None = None,
    ) -> None:
        """Initializes type handler.

        Args:
            format_default: Function for formatting default value
            get_example: Function for generating example
            type_name: Type name (if None, taken from type.__name__)
        """
        self.format_default = format_default
        self.get_example = get_example
        self.type_name = type_name


TYPE_HANDLERS: dict[type, TypeHandler] = {
    str: TypeHandler(
        format_default=str,
        get_example=lambda: "your_value_here",
        type_name="str",
    ),
    int: TypeHandler(
        format_default=str,
        get_example=lambda: "0",
        type_name="int",
    ),
    float: TypeHandler(
        format_default=str,
        get_example=lambda: "0.0",
        type_name="float",
    ),
    bool: TypeHandler(
        format_default=lambda v: str(v).lower(),
        get_example=lambda: "true",
        type_name="bool",
    ),
    dict: TypeHandler(
        format_default=json.dumps,
        get_example=lambda: '{"key": "value"}',
        type_name="dict",
    ),
}


class DocumentationGenerator:
    """Documentation generator for EnvSchema.

    Attributes:
        schema_class: EnvSchema schema class
        prefix: Prefix for environment variables
    """

    def __init__(
        self,
        schema_class: type["EnvSchema"],
        prefix: str | None = None,
    ) -> None:
        """Initializes generator.

        Args:
            schema_class: EnvSchema schema class
            prefix: Prefix for environment variables (default: "")
        """
        self.schema_class = schema_class
        self.prefix = prefix or ""
        self._metadata_cache: list[dict[str, Any]] | None = None

    @staticmethod
    def _is_nested_schema(field_type: type) -> bool:
        """Checks if type is nested schema.

        Args:
            field_type: Field type

        Returns:
            True if type is subclass of EnvSchema
        """
        from .schema import EnvSchema

        try:
            return isinstance(field_type, type) and issubclass(field_type, EnvSchema)
        except TypeError:
            return False

    def _collect_metadata(self) -> list[dict[str, Any]]:
        """Collects schema fields metadata (including nested).

        Returns:
            List of dictionaries with metadata for each field
        """
        return self._collect_fields_recursive(self.schema_class, self.prefix)

    def _collect_fields_recursive(
        self, schema_class: type["EnvSchema"], parent_prefix: str
    ) -> list[dict[str, Any]]:
        """Recursively collects fields from schema and nested schemas.

        Args:
            schema_class: Schema class
            parent_prefix: Parent schema prefix

        Returns:
            List of fields metadata
        """
        fields = schema_class._get_fields()
        metadata = []

        for field_name, (field, field_type) in fields.items():
            if self._is_nested_schema(field_type):
                nested_prefix = self._compute_nested_prefix(
                    field, field_name, parent_prefix
                )
                nested_metadata = self._collect_fields_recursive(
                    field_type, nested_prefix
                )
                metadata.extend(nested_metadata)
            else:
                env_name = field.get_env_name(parent_prefix)

                is_optional = is_optional_type(field_type)
                is_required = not field.has_default() and not is_optional

                default_value = field.get_default() if field.has_default() else None
                description = field.description or ""

                metadata.append(
                    {
                        "field_name": field_name,
                        "env_name": env_name,
                        "field_type": field_type,
                        "is_required": is_required,
                        "default_value": default_value,
                        "description": description,
                    }
                )

        return metadata

    @staticmethod
    def _compute_nested_prefix(field: Any, field_name: str, parent_prefix: str) -> str:
        """Computes prefix for nested schema.

        Args:
            field: Field descriptor
            field_name: Field name in schema
            parent_prefix: Parent schema prefix

        Returns:
            Full prefix for nested schema
        """
        if field.prefix:
            nested_prefix: str = field.prefix
        else:
            nested_prefix = f"{field_name.upper()}_"

        if parent_prefix:
            return f"{parent_prefix}{nested_prefix}"

        return nested_prefix

    def _get_field_metadata(self) -> list[dict[str, Any]]:
        """Gets fields metadata (with caching).

        Returns:
            List of dictionaries with metadata for each field
        """
        if self._metadata_cache is None:
            self._metadata_cache = self._collect_metadata()
        return self._metadata_cache

    def _get_handler_for_type(self, field_type: type) -> TypeHandler:
        """Gets handler for data type.

        Args:
            field_type: Field type

        Returns:
            Type handler
        """
        origin = get_origin(field_type)

        if is_optional_type(field_type):
            inner_type = get_optional_inner_type(field_type)
            inner_handler = self._get_handler_for_type(inner_type)

            return TypeHandler(
                format_default=lambda v: (
                    "" if v is None else inner_handler.format_default(v)
                ),
                get_example=inner_handler.get_example,
                type_name=f"Optional[{inner_handler.type_name}]",
            )

        if origin is list:
            args = get_args(field_type)
            item_type = args[0] if args else str

            if item_type is str:
                return TypeHandler(
                    format_default=lambda v: ",".join(str(item) for item in v),
                    get_example=lambda: "value1,value2",
                    type_name=f"list[{item_type.__name__}]",
                )
            else:
                return TypeHandler(
                    format_default=json.dumps,
                    get_example=lambda: "[1, 2, 3]",
                    type_name=f"list[{item_type.__name__}]",
                )

        if field_type in TYPE_HANDLERS:
            return TYPE_HANDLERS[field_type]

        return TypeHandler(
            format_default=str,
            get_example=lambda: "your_value_here",
            type_name=getattr(field_type, "__name__", str(field_type)),
        )

    def _format_default_value(self, value: Any, field_type: type) -> str:
        """Formats default value for .env file.

        Args:
            value: Default value
            field_type: Field type

        Returns:
            Formatted string value
        """
        if value is None:
            return ""

        handler = self._get_handler_for_type(field_type)
        return handler.format_default(value)

    def _get_example_value(self, field_type: type) -> str:
        """Gets example value for required field.

        Args:
            field_type: Field type

        Returns:
            Example value
        """
        handler = self._get_handler_for_type(field_type)
        return handler.get_example()

    def _format_type_name(self, field_type: type) -> str:
        """Formats type name for documentation.

        Args:
            field_type: Field type

        Returns:
            String representation of type
        """
        handler = self._get_handler_for_type(field_type)
        if handler.type_name:
            return handler.type_name

        type_name = getattr(field_type, "__name__", str(field_type))
        return str(type_name)

    def _escape_markdown(self, text: str) -> str:
        """Escapes special Markdown characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        if not text:
            return ""

        replacements = [
            ("\\", "\\\\"),
            ("|", "\\|"),
            ("_", "\\_"),
            ("*", "\\*"),
            ("[", "\\["),
            ("]", "\\]"),
            ("`", "\\`"),
        ]

        for old, new in replacements:
            text = text.replace(old, new)

        return text

    def generate_example_env(self, path: str | None = None) -> str:
        """Generates .env.example file.

        Args:
            path: Path to file for writing. If None, returns string

        Returns:
            Content of .env.example file
        """
        metadata = self._get_field_metadata()
        lines = []

        for field_info in metadata:
            env_name = field_info["env_name"]
            description = field_info["description"]
            is_required = field_info["is_required"]
            default_value = field_info["default_value"]
            field_type = field_info["field_type"]

            comment_parts = []
            if description:
                comment_parts.append(description)

            if not is_required and default_value is not None:
                formatted_default = self._format_default_value(
                    default_value, field_type
                )
                comment_parts.append(f"default: {formatted_default}")

            if is_required:
                comment_parts.append("required")

            if comment_parts:
                comment = " ".join(comment_parts)
                lines.append(f"# {comment}")

            if is_required:
                example_value = self._get_example_value(field_type)
                lines.append(f"{env_name}={example_value}")
            else:
                formatted_value = self._format_default_value(default_value, field_type)
                lines.append(f"{env_name}={formatted_value}")

            lines.append("")

        content = "\n".join(lines).rstrip() + "\n"

        if path:
            Path(path).write_text(content, encoding="utf-8")

        return content

    def generate_markdown_docs(self) -> str:
        """Generates Markdown documentation.

        Returns:
            Full Markdown document with environment variables description
        """
        metadata = self._get_field_metadata()
        schema_name = self.schema_class.__name__

        lines = [
            "# Environment Variables Configuration",
            "",
            (
                "This document describes environment variables for "
                f"`{schema_name}` schema."
            ),
            "",
        ]

        required_count = sum(1 for m in metadata if m["is_required"])
        optional_count = len(metadata) - required_count

        lines.extend(
            [
                "## Overview",
                "",
                f"- **Total variables**: {len(metadata)}",
                f"- **Required**: {required_count}",
                f"- **Optional**: {optional_count}",
            ]
        )

        if self.prefix:
            lines.append(f"- **Prefix**: `{self.prefix}`")

        lines.extend(["", "## Variables", ""])

        lines.extend(
            [
                "| Variable | Type | Required | Default | Description |",
                "|----------|------|----------|---------|-------------|",
            ]
        )

        for field_info in metadata:
            env_name = field_info["env_name"]
            field_type = field_info["field_type"]
            is_required = field_info["is_required"]
            default_value = field_info["default_value"]
            description = field_info["description"]

            type_str = self._format_type_name(field_type)
            required_str = "**Yes**" if is_required else "No"
            default_str = (
                f"`{self._format_default_value(default_value, field_type)}`"
                if default_value is not None
                else "-"
            )

            description_escaped = (
                self._escape_markdown(description)
                if description
                else "*No description*"
            )

            lines.append(
                f"| `{env_name}` | `{type_str}` | {required_str} | "
                f"{default_str} | {description_escaped} |"
            )

        lines.extend(["", "## Usage Example", ""])
        lines.append("Create a `.env` file in your project root:")
        lines.extend(["", "```bash"])

        for field_info in metadata[:5]:
            env_name = field_info["env_name"]
            is_required = field_info["is_required"]
            default_value = field_info["default_value"]
            field_type = field_info["field_type"]

            if is_required:
                example_value = self._get_example_value(field_type)
                lines.append(f"{env_name}={example_value}")
            elif default_value is not None:
                formatted_value = self._format_default_value(default_value, field_type)
                lines.append(f"{env_name}={formatted_value}")

        if len(metadata) > 5:
            lines.append("# ... (other variables)")

        lines.extend(["```", ""])

        lines.extend(
            [
                "## Notes",
                "",
                "- **Required** variables must be set before running the application",
                "- Variables with defaults are optional and use them if not set",
                "- Boolean values: `true`, `false`, `yes`, `no`, `1`, `0`, `on`, `off`",
                "- List values accept comma-separated values or JSON arrays",
                "",
            ]
        )

        return "\n".join(lines)
