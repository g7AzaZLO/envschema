import json
from collections.abc import Callable
from typing import Any, TypeVar, Union, cast, get_args, get_origin

T = TypeVar("T")
CasterFunc = Callable[[str], Any]


def cast_str(value: str) -> str:
    """Casts value to string.

    Args:
        value: String value from environment

    Returns:
        Original string unchanged
    """
    return value


def cast_int(value: str) -> int:
    """Casts value to integer.

    Args:
        value: String value from environment

    Returns:
        Integer value

    Raises:
        ValueError: If value cannot be converted to int
    """
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"cannot cast '{value}' to int") from None


def cast_float(value: str) -> float:
    """Casts value to float.

    Args:
        value: String value from environment

    Returns:
        Float value

    Raises:
        ValueError: If value cannot be converted to float
    """
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"cannot cast '{value}' to float") from None


def cast_bool(value: str) -> bool:
    """Casts value to boolean.

    Supported values:
    - True: "true", "yes", "1", "on" (case-insensitive)
    - False: "false", "no", "0", "off" (case-insensitive)

    Args:
        value: String value from environment

    Returns:
        Boolean value

    Raises:
        ValueError: If value is not recognized as bool
    """
    normalized = value.lower().strip()

    if normalized in ("true", "yes", "1", "on"):
        return True
    elif normalized in ("false", "no", "0", "off"):
        return False
    else:
        raise ValueError(
            f"invalid boolean value '{value}' (expected: true/false/yes/no/1/0/on/off)"
        )


def cast_list(value: str, item_type: type = str) -> list:
    """Casts value to list.

    Automatically detects format:
    - If string looks like JSON array → parses as JSON
    - Otherwise → parses as CSV (separator: comma)

    Args:
        value: String value from environment
        item_type: Type of list items (default: str)

    Returns:
        List of items of specified type

    Raises:
        ValueError: If value cannot be parsed
    """
    stripped = value.strip()

    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            parsed = json.loads(stripped)
            if not isinstance(parsed, list):
                raise ValueError(f"expected JSON array, got {type(parsed)}")

            if item_type is not str:
                caster = _get_caster_for_type(item_type)
                return [caster(str(item)) for item in parsed]
            return parsed

        except json.JSONDecodeError as e:
            raise ValueError(f"invalid JSON array: {e}") from e

    if not stripped:
        return []

    items = [item.strip() for item in stripped.split(",")]

    if item_type is not str:
        caster = _get_caster_for_type(item_type)
        try:
            return [caster(item) for item in items]
        except ValueError as e:
            raise ValueError(
                f"cannot cast list items to {_get_type_name(item_type)}: {e}"
            ) from e

    return items


def cast_dict(value: str) -> dict:
    """Casts value to dictionary via JSON.

    Args:
        value: String value from environment (JSON format)

    Returns:
        Dictionary

    Raises:
        ValueError: If value cannot be parsed as JSON object
    """
    try:
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError(f"expected JSON object, got {type(parsed).__name__}")
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON object: {e}") from e


_CASTERS: dict[type, CasterFunc] = {
    str: cast_str,
    int: cast_int,
    float: cast_float,
    bool: cast_bool,
    dict: cast_dict,
}


def register_caster(type_: type, caster: CasterFunc) -> None:
    """Registers custom caster for type.

    Args:
        type_: Data type
        caster: Casting function (str -> type_)

    Example:
        >>> def cast_timedelta(value: str) -> timedelta:
        ...     return timedelta(seconds=int(value))
        >>> register_caster(timedelta, cast_timedelta)
    """
    _CASTERS[type_] = caster


def _get_caster_for_type(type_: type) -> CasterFunc:
    """Gets casting function for type.

    Args:
        type_: Data type

    Returns:
        Casting function

    Raises:
        ValueError: If caster for type is not found
    """
    if type_ in _CASTERS:
        return _CASTERS[type_]

    raise ValueError(f"no caster registered for type {type_}")


def is_optional_type(type_: type) -> bool:
    """Checks if type is Optional[T] or Union[T, None].

    Args:
        type_: Type to check

    Returns:
        True if type is Optional[T] or Union[T, None]
    """
    origin = get_origin(type_)

    if origin is Union:
        args = get_args(type_)
        return len(args) == 2 and type(None) in args

    try:
        import types

        if hasattr(types, "UnionType") and isinstance(type_, types.UnionType):
            args = get_args(type_)
            return len(args) == 2 and type(None) in args
    except (ImportError, AttributeError):
        pass

    return False


def get_optional_inner_type(type_: type) -> type:
    """Extracts inner type T from Optional[T].

    Args:
        type_: Optional type

    Returns:
        Inner type T

    Raises:
        ValueError: If type is not Optional
    """
    if not is_optional_type(type_):
        raise ValueError(f"type {type_} is not Optional")

    args = get_args(type_)

    for arg in args:
        if arg is not type(None):
            return cast(type, arg)

    raise ValueError(f"cannot extract inner type from {type_}")


def _get_type_name(type_: type) -> str:
    """Safely gets type name for display.

    Handles all cases including UnionType, Optional, list[T], etc.

    Args:
        type_: Data type

    Returns:
        String representation of type name
    """
    if is_optional_type(type_):
        inner_type = get_optional_inner_type(type_)
        inner_name = _get_type_name(inner_type)
        return f"Optional[{inner_name}]"

    origin = get_origin(type_)
    if origin is list:
        args = get_args(type_)
        item_type = args[0] if args else str
        item_name = _get_type_name(item_type)
        return f"list[{item_name}]"

    return getattr(type_, "__name__", str(type_))


def cast_value(value: str, type_: type) -> Any:
    """Casts value to specified type.

    Supports basic types, list[T] and Optional[T].

    Args:
        value: String value from environment
        type_: Target data type

    Returns:
        Value of specified type

    Raises:
        ValueError: If casting is impossible
    """
    if is_optional_type(type_):
        inner_type = get_optional_inner_type(type_)
        return cast_value(value, inner_type)

    origin = get_origin(type_)

    if origin is list:
        args = get_args(type_)
        item_type = args[0] if args else str
        return cast_list(value, item_type)

    caster = _get_caster_for_type(type_)
    return caster(value)
