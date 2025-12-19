import pytest

from envschema.casters import (
    cast_bool,
    cast_dict,
    cast_float,
    cast_int,
    cast_list,
    cast_str,
    cast_value,
    register_caster,
)


class TestCastStr:
    """Tests for cast_str."""

    def test_returns_string_as_is(self) -> None:
        """Checks that string is returned unchanged."""
        assert cast_str("hello") == "hello"
        assert cast_str("123") == "123"
        assert cast_str("") == ""


class TestCastInt:
    """Tests for cast_int."""

    def test_valid_integer(self) -> None:
        """Checks casting of valid integers."""
        assert cast_int("123") == 123
        assert cast_int("0") == 0
        assert cast_int("-42") == -42

    def test_invalid_integer(self) -> None:
        """Checks error on invalid value."""
        with pytest.raises(ValueError, match="cannot cast 'abc' to int"):
            cast_int("abc")

        with pytest.raises(ValueError, match="cannot cast '12.5' to int"):
            cast_int("12.5")


class TestCastFloat:
    """Tests for cast_float."""

    def test_valid_float(self) -> None:
        """Checks casting of valid floats."""
        assert cast_float("123.5") == 123.5
        assert cast_float("0.0") == 0.0
        assert cast_float("-42.7") == -42.7
        assert cast_float("123") == 123.0

    def test_invalid_float(self) -> None:
        """Checks error on invalid value."""
        with pytest.raises(ValueError, match="cannot cast 'abc' to float"):
            cast_float("abc")


class TestCastBool:
    """Tests for cast_bool."""

    def test_true_values(self) -> None:
        """Checks casting of True values."""
        assert cast_bool("true") is True
        assert cast_bool("True") is True
        assert cast_bool("TRUE") is True
        assert cast_bool("yes") is True
        assert cast_bool("YES") is True
        assert cast_bool("1") is True
        assert cast_bool("on") is True
        assert cast_bool("ON") is True

    def test_false_values(self) -> None:
        """Checks casting of False values."""
        assert cast_bool("false") is False
        assert cast_bool("False") is False
        assert cast_bool("FALSE") is False
        assert cast_bool("no") is False
        assert cast_bool("NO") is False
        assert cast_bool("0") is False
        assert cast_bool("off") is False
        assert cast_bool("OFF") is False

    def test_invalid_bool(self) -> None:
        """Checks error on invalid value."""
        with pytest.raises(ValueError, match="invalid boolean value 'maybe'"):
            cast_bool("maybe")

        with pytest.raises(ValueError, match="invalid boolean value '2'"):
            cast_bool("2")


class TestCastList:
    """Tests for cast_list."""

    def test_json_array_string_list(self) -> None:
        """Checks parsing of JSON string array."""
        result = cast_list('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_json_array_int_list(self) -> None:
        """Checks parsing of JSON number array."""
        result = cast_list("[1, 2, 3]", item_type=int)
        assert result == [1, 2, 3]

    def test_csv_string_list(self) -> None:
        """Checks parsing of CSV string."""
        result = cast_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_csv_int_list(self) -> None:
        """Checks parsing of CSV string with int casting."""
        result = cast_list("1,2,3", item_type=int)
        assert result == [1, 2, 3]

    def test_empty_list(self) -> None:
        """Checks handling of empty list."""
        assert cast_list("") == []
        assert cast_list("[]") == []

    def test_invalid_json_array(self) -> None:
        """Checks error on invalid JSON."""
        with pytest.raises(ValueError, match="invalid JSON array"):
            cast_list("[invalid json]")

    def test_invalid_list_items(self) -> None:
        """Checks error on invalid list items."""
        with pytest.raises(ValueError, match="cannot cast list items to int"):
            cast_list("1,abc,3", item_type=int)


class TestCastDict:
    """Tests for cast_dict."""

    def test_valid_json_object(self) -> None:
        """Checks parsing of valid JSON object."""
        result = cast_dict('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_invalid_json_object(self) -> None:
        """Checks error on invalid JSON."""
        with pytest.raises(ValueError, match="invalid JSON object"):
            cast_dict("{invalid json")

    def test_not_a_dict(self) -> None:
        """Checks error if JSON is not an object."""
        with pytest.raises(ValueError, match="expected JSON object"):
            cast_dict('["array", "not", "object"]')


class TestCastValue:
    """Tests for cast_value."""

    def test_basic_types(self) -> None:
        """Checks casting of basic types."""
        assert cast_value("123", int) == 123
        assert cast_value("45.6", float) == 45.6
        assert cast_value("hello", str) == "hello"
        assert cast_value("true", bool) is True

    def test_list_type(self) -> None:
        """Checks casting of lists."""
        result = cast_value("1,2,3", list[int])
        assert result == [1, 2, 3]

        result = cast_value('["a", "b"]', list[str])
        assert result == ["a", "b"]

    def test_unknown_type(self) -> None:
        """Checks error for unknown type."""
        with pytest.raises(ValueError, match="no caster registered"):
            cast_value("value", tuple)  # type: ignore[arg-type]


class TestRegisterCaster:
    """Tests for register_caster."""

    def test_register_custom_caster(self) -> None:
        """Checks registration of custom caster."""

        def cast_uppercase(value: str) -> str:
            return value.upper()

        register_caster(str, cast_uppercase)
        result = cast_value("hello", str)
        assert result == "HELLO"

        from envschema.casters import cast_str

        register_caster(str, cast_str)
