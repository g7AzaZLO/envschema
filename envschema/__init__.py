"""envschema - minimalistic library for working with environment variables.

Type-safe loading, casting and validation of environment variables
based on type annotations.

Usage example:
    >>> from envschema import EnvSchema, Field
    >>>
    >>> class Settings(EnvSchema):
    ...     port: int
    ...     debug: bool = Field(default=False)
    ...     database_url: str = Field(env="DATABASE_URL")
    >>>
    >>> settings = Settings.load()
    >>> print(settings.port)
"""

from .casters import register_caster
from .errors import EnvSchemaError, ValidationError
from .field import Field
from .loader import load_dotenv, load_env_with_dotenv
from .schema import EnvSchema

__version__ = "0.1.0"

__all__ = [
    "EnvSchema",
    "Field",
    "EnvSchemaError",
    "ValidationError",
    "register_caster",
    "load_dotenv",
    "load_env_with_dotenv",
]
