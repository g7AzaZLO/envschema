import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envschema.loader import (
    load_dotenv,
    load_env_with_dotenv,
    merge_env_sources,
)


@pytest.fixture(autouse=True)
def mock_dotenv() -> None:
    """Mocks dotenv module for all tests."""
    mock_dotenv_module = MagicMock()
    mock_dotenv_module.dotenv_values = MagicMock()
    mock_dotenv_module.find_dotenv = MagicMock()

    with patch.dict("sys.modules", {"dotenv": mock_dotenv_module}):
        yield


class TestLoadDotenv:
    """Tests for load_dotenv function."""

    def test_load_dotenv_with_string_path(self) -> None:
        """Checks loading .env file by string path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("KEY1=value1\nKEY2=value2\nKEY3=value3\n")
            temp_path = f.name

        try:
            sys.modules["dotenv"].dotenv_values.return_value = {
                "KEY1": "value1",
                "KEY2": "value2",
                "KEY3": "value3",
            }

            result = load_dotenv(temp_path)
            assert result == {
                "KEY1": "value1",
                "KEY2": "value2",
                "KEY3": "value3",
            }
            sys.modules["dotenv"].dotenv_values.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_dotenv_with_path_object(self) -> None:
        """Checks loading .env file by Path object."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_KEY=test_value\n")
            temp_path = Path(f.name)

        try:
            sys.modules["dotenv"].dotenv_values.return_value = {
                "TEST_KEY": "test_value"
            }

            result = load_dotenv(temp_path)
            assert result == {"TEST_KEY": "test_value"}
            sys.modules["dotenv"].dotenv_values.assert_called_once_with(str(temp_path))
        finally:
            os.unlink(str(temp_path))

    def test_load_dotenv_with_bool_true(self, tmp_path: Path) -> None:
        """Checks auto-search of .env file when dotenv_path=True."""
        env_file = tmp_path / ".env"
        env_file.write_text("AUTO_KEY=auto_value\n")
        sys.modules["dotenv"].find_dotenv.return_value = str(env_file)
        sys.modules["dotenv"].dotenv_values.return_value = {"AUTO_KEY": "auto_value"}

        result = load_dotenv(True)
        assert result == {"AUTO_KEY": "auto_value"}
        sys.modules["dotenv"].find_dotenv.assert_called_once_with(usecwd=True)

    def test_load_dotenv_with_bool_true_not_found(self) -> None:
        """Checks error on auto-search if file not found."""
        sys.modules["dotenv"].find_dotenv.return_value = ""

        with pytest.raises(FileNotFoundError) as exc_info:
            load_dotenv(True)

        assert ".env file not found in current or parent directories" in str(
            exc_info.value
        )

    def test_load_dotenv_with_bool_false(self) -> None:
        """Checks returning empty dict when dotenv_path=False."""
        result = load_dotenv(False)
        assert result == {}

    def test_load_dotenv_filters_none_values(self) -> None:
        """Checks filtering None values from .env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("KEY1=value1\nKEY2=\nKEY3=value3\n")
            temp_path = f.name

        try:
            sys.modules["dotenv"].dotenv_values.return_value = {
                "KEY1": "value1",
                "KEY2": None,
                "KEY3": "value3",
            }

            result = load_dotenv(temp_path)
            assert "KEY1" in result
            assert "KEY2" not in result
            assert "KEY3" in result
            assert result["KEY1"] == "value1"
            assert result["KEY3"] == "value3"
        finally:
            os.unlink(temp_path)

    def test_load_dotenv_file_not_found(self) -> None:
        """Checks error when .env file is missing."""
        non_existent = Path("/non/existent/path/.env")

        with pytest.raises(FileNotFoundError) as exc_info:
            load_dotenv(non_existent)

        assert ".env file not found" in str(exc_info.value)
        assert str(non_existent) in str(exc_info.value)

    def test_load_dotenv_import_error(self) -> None:
        """Checks error when python-dotenv is missing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            temp_path = f.name

        try:
            with patch.dict("sys.modules", {"dotenv": None}):
                with pytest.raises(ImportError) as exc_info:
                    load_dotenv(temp_path)

                error_msg = str(exc_info.value)
                assert "python-dotenv is required" in error_msg
                assert "pip install" in error_msg
        finally:
            os.unlink(temp_path)


class TestMergeEnvSources:
    """Tests for merge_env_sources function."""

    def test_merge_basic(self) -> None:
        """Checks basic merging of variables."""
        dotenv_vars = {"KEY1": "dotenv_value1", "KEY2": "dotenv_value2"}
        system_env = {"KEY2": "system_value2", "KEY3": "system_value3"}

        result = merge_env_sources(dotenv_vars, system_env)

        assert result["KEY1"] == "dotenv_value1"
        assert result["KEY2"] == "system_value2"
        assert result["KEY3"] == "system_value3"

    def test_merge_system_env_priority(self) -> None:
        """Checks system_env priority over dotenv_vars."""
        dotenv_vars = {"CONFLICT_KEY": "dotenv_value"}
        system_env = {"CONFLICT_KEY": "system_value"}

        result = merge_env_sources(dotenv_vars, system_env)

        assert result["CONFLICT_KEY"] == "system_value"

    def test_merge_with_none_system_env(self) -> None:
        """Checks using os.environ when system_env=None."""
        dotenv_vars = {"DOTENV_KEY": "dotenv_value"}

        original_env = dict(os.environ)

        try:
            os.environ.clear()
            os.environ["SYSTEM_KEY"] = "system_value"
            os.environ["DOTENV_KEY"] = "system_override"

            result = merge_env_sources(dotenv_vars, None)

            assert result["DOTENV_KEY"] == "system_override"
            assert result["SYSTEM_KEY"] == "system_value"
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_merge_empty_dotenv(self) -> None:
        """Checks merging with empty dotenv_vars."""
        system_env = {"KEY1": "value1", "KEY2": "value2"}

        result = merge_env_sources({}, system_env)

        assert result == system_env

    def test_merge_empty_system_env(self) -> None:
        """Checks merging with empty system_env."""
        dotenv_vars = {"KEY1": "value1", "KEY2": "value2"}

        result = merge_env_sources(dotenv_vars, {})

        assert result == dotenv_vars

    def test_merge_both_empty(self) -> None:
        """Checks merging two empty dictionaries."""
        result = merge_env_sources({}, {})

        assert result == {}


class TestLoadEnvWithDotenv:
    """Tests for load_env_with_dotenv function."""

    def test_load_with_none_dotenv_path(self) -> None:
        """Checks loading only os.environ when dotenv_path=None."""
        original_env = dict(os.environ)

        try:
            os.environ.clear()
            os.environ["TEST_KEY"] = "test_value"

            result = load_env_with_dotenv(dotenv_path=None)

            assert "TEST_KEY" in result
            assert result["TEST_KEY"] == "test_value"
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_load_with_string_path(self) -> None:
        """Checks loading with string path specified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("DOTENV_KEY=dotenv_value\n")
            temp_path = f.name

        original_env = dict(os.environ)

        try:
            os.environ.clear()
            os.environ["SYSTEM_KEY"] = "system_value"
            os.environ["DOTENV_KEY"] = "system_override"

            sys.modules["dotenv"].dotenv_values.return_value = {
                "DOTENV_KEY": "dotenv_value"
            }

            result = load_env_with_dotenv(dotenv_path=temp_path, override=False)

            assert result["DOTENV_KEY"] == "system_override"
            assert result["SYSTEM_KEY"] == "system_value"
        finally:
            os.unlink(temp_path)
            os.environ.clear()
            os.environ.update(original_env)

    def test_load_with_path_object(self) -> None:
        """Checks loading with Path object specified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("PATH_KEY=path_value\n")
            temp_path = Path(f.name)

        original_env = dict(os.environ)

        try:
            os.environ.clear()
            sys.modules["dotenv"].dotenv_values.return_value = {
                "PATH_KEY": "path_value"
            }

            result = load_env_with_dotenv(dotenv_path=temp_path)

            assert result["PATH_KEY"] == "path_value"
        finally:
            os.unlink(str(temp_path))
            os.environ.clear()
            os.environ.update(original_env)

    def test_load_with_bool_true(self, tmp_path: Path) -> None:
        """Checks auto-search of .env file when dotenv_path=True."""
        env_file = tmp_path / ".env"
        env_file.write_text("AUTO_KEY=auto_value\n")

        original_env = dict(os.environ)

        try:
            os.environ.clear()
            sys.modules["dotenv"].find_dotenv.return_value = str(env_file)
            sys.modules["dotenv"].dotenv_values.return_value = {
                "AUTO_KEY": "auto_value"
            }

            result = load_env_with_dotenv(dotenv_path=True)

            assert result["AUTO_KEY"] == "auto_value"
            sys.modules["dotenv"].find_dotenv.assert_called_once_with(usecwd=True)
        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_load_with_override_false(self) -> None:
        """Checks override=False mode (system_env has priority)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("CONFLICT_KEY=dotenv_value\n")
            temp_path = f.name

        original_env = dict(os.environ)

        try:
            os.environ.clear()
            os.environ["CONFLICT_KEY"] = "system_value"

            sys.modules["dotenv"].dotenv_values.return_value = {
                "CONFLICT_KEY": "dotenv_value"
            }

            result = load_env_with_dotenv(dotenv_path=temp_path, override=False)

            assert result["CONFLICT_KEY"] == "system_value"
        finally:
            os.unlink(temp_path)
            os.environ.clear()
            os.environ.update(original_env)

    def test_load_with_override_true(self) -> None:
        """Checks override=True mode (dotenv overrides system)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("CONFLICT_KEY=dotenv_value\n")
            temp_path = f.name

        original_env = dict(os.environ)

        try:
            os.environ.clear()
            os.environ["CONFLICT_KEY"] = "system_value"
            os.environ["SYSTEM_ONLY_KEY"] = "system_only"

            sys.modules["dotenv"].dotenv_values.return_value = {
                "CONFLICT_KEY": "dotenv_value"
            }

            result = load_env_with_dotenv(dotenv_path=temp_path, override=True)

            assert result["CONFLICT_KEY"] == "dotenv_value"
            assert result["SYSTEM_ONLY_KEY"] == "system_only"
        finally:
            os.unlink(temp_path)
            os.environ.clear()
            os.environ.update(original_env)

    def test_load_file_not_found(self) -> None:
        """Checks error when .env file is missing."""
        non_existent = Path("/non/existent/path/.env")

        with pytest.raises(FileNotFoundError):
            load_env_with_dotenv(dotenv_path=non_existent)
