import os
from pathlib import Path


def load_dotenv(dotenv_path: str | Path | bool) -> dict[str, str]:
    """Loads variables from .env file.

    When dotenv_path=True, performs recursive search for .env file upward
    through directory tree from current working directory to project root.

    Args:
        dotenv_path: Path to .env file, True for auto-search, or False

    Returns:
        Dictionary of environment variables from file

    Raises:
        ImportError: If python-dotenv is not installed
        FileNotFoundError: If specified file does not exist
    """
    try:
        from dotenv import dotenv_values  # type: ignore[import-not-found]
        from dotenv import (
            find_dotenv as find_dotenv_util,  # type: ignore[import-not-found]
        )
    except ImportError as e:
        raise ImportError(
            "python-dotenv is required for .env file support. "
            "Install it with: pip install envschema[dotenv] "
            "or pip install python-dotenv"
        ) from e

    if isinstance(dotenv_path, bool):
        if dotenv_path:
            found_path = find_dotenv_util(usecwd=True)
            if not found_path:
                raise FileNotFoundError(
                    ".env file not found in current or parent directories"
                )
            file_path = Path(found_path)
        else:
            return {}
    else:
        file_path = Path(dotenv_path)

    if not file_path.exists():
        raise FileNotFoundError(f".env file not found: {file_path}")

    env_vars = dotenv_values(str(file_path))
    return {k: v for k, v in env_vars.items() if v is not None}


def merge_env_sources(
    dotenv_vars: dict[str, str],
    system_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Merges variables from .env and system environment.

    Priority: system_env > dotenv_vars
    (system variables override values from .env)

    Args:
        dotenv_vars: Variables from .env file
        system_env: System environment variables (default: os.environ)

    Returns:
        Merged dictionary of variables
    """
    if system_env is None:
        system_env = dict(os.environ)

    merged = {}
    merged.update(dotenv_vars)
    merged.update(system_env)

    return merged


def load_env_with_dotenv(
    dotenv_path: str | Path | bool | None = None,
    override: bool = False,
) -> dict[str, str]:
    """Loads environment variables with .env file support.

    Args:
        dotenv_path: Path to .env file, True for auto-search, None to ignore
        override: If True, .env overrides system variables

    Returns:
        Dictionary of environment variables

    Example:
        >>> env = load_env_with_dotenv(".env")
        >>> env = load_env_with_dotenv(True)  # Auto-search .env
        >>> env = load_env_with_dotenv()  # Only os.environ
    """
    if dotenv_path is None:
        return dict(os.environ)

    dotenv_vars = load_dotenv(dotenv_path)

    if override:
        merged = dict(os.environ)
        merged.update(dotenv_vars)
        return merged
    else:
        return merge_env_sources(dotenv_vars)
