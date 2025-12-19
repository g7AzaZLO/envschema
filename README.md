# EnvSchema

<div align="center">

![PyPI - Version](https://img.shields.io/pypi/v/envschema?color=blue)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/envschema)
![License](https://img.shields.io/github/license/g7azazlo/envschema)

**Type-safe environment variables with automatic validation and documentation generation**

[Documentation](#documentation) | [Installation](#installation) | [Quick Start](#quick-start) | [Examples](#examples) | [Читать на русском](README_ru.md)

</div>

---

## 🎯 Overview

**EnvSchema** is a lightweight Python library for managing environment variables with automatic type validation, nested schemas support, and built-in documentation generation. It eliminates boilerplate code and provides type safety for your application configuration.

## ✨ Key Features

- 🔒 **Type-safe**: Full typing support with automatic validation
- 🎨 **Clean syntax**: Pythonic API using dataclass-like definitions
- 🏗️ **Nested schemas**: Support for complex hierarchical configurations
- 📝 **Auto-documentation**: Generate `.env.example` and Markdown docs automatically
- 🔄 **Flexible types**: Support for `str`, `int`, `float`, `bool`, `list`, `dict`, `Optional`
- 🌐 **`.env` support**: Load variables from `.env` files (requires `python-dotenv`)
- ⚡ **Zero dependencies**: Core functionality works without external packages
- 🎯 **Clear errors**: Detailed validation error messages

## 📦 Installation

```bash
# Basic installation
pip install envschema

# With .env file support
pip install envschema[dotenv]
# or
pip install envschema python-dotenv
```

## 🚀 Quick Start

### Basic Example

```python
from envschema import EnvSchema, Field

class Settings(EnvSchema):
    # Required fields
    api_key: str
    database_url: str
    
    # Optional fields with defaults
    debug: bool = False
    port: int = 8000
    
    # Field with custom env name and description
    secret: str = Field(
        env="SECRET_KEY",
        description="Secret key for encryption"
    )
    
    # Optional field
    redis_url: str | None = None

# Load from environment variables
settings = Settings.load()

# Access values
print(settings.api_key)
print(settings.port)
```

### With `.env` File

```python
# Load from .env file
settings = Settings.load(dotenv_path=".env")

# Auto-discover .env file in current or parent directories
settings = Settings.load(dotenv_path=True)

# Override system env with .env values
settings = Settings.load(dotenv_path=".env", dotenv_override=True)
```

## 📚 Examples

### Supported Types

```python
from envschema import EnvSchema

class Config(EnvSchema):
    # String
    name: str = "default"
    
    # Integer
    workers: int = 4
    
    # Float
    timeout: float = 30.5
    
    # Boolean (accepts: true/false, yes/no, 1/0, on/off)
    enabled: bool = True
    
    # List (comma-separated or JSON array)
    hosts: list[str] = ["localhost"]
    allowed_ids: list[int] = [1, 2, 3]
    
    # Dict (JSON object)
    metadata: dict = {"version": "1.0"}
    
    # Optional
    optional_value: str | None = None
```

**Environment variables:**

```bash
NAME=myapp
WORKERS=8
TIMEOUT=60.0
ENABLED=true
HOSTS=host1,host2,host3
ALLOWED_IDS=[10, 20, 30]
METADATA={"key": "value"}
```

### Nested Schemas

```python
from envschema import EnvSchema, Field

class DatabaseConfig(EnvSchema):
    host: str = "localhost"
    port: int = 5432
    name: str
    user: str
    password: str

class RedisConfig(EnvSchema):
    host: str = "localhost"
    port: int = 6379

class Settings(EnvSchema):
    # Nested schemas with auto prefix
    database: DatabaseConfig
    redis: RedisConfig
    
    # Nested schema with custom prefix
    cache: RedisConfig = Field(prefix="CACHE_")

# Load configuration
settings = Settings.load()

# Access nested values
print(settings.database.host)
print(settings.redis.port)
```

**Environment variables:**

```bash
# Database config (prefix: DATABASE_)
DATABASE_HOST=db.example.com
DATABASE_PORT=5432
DATABASE_NAME=mydb
DATABASE_USER=admin
DATABASE_PASSWORD=secret123

# Redis config (prefix: REDIS_)
REDIS_HOST=redis.example.com
REDIS_PORT=6379

# Cache config (custom prefix: CACHE_)
CACHE_HOST=cache.example.com
CACHE_PORT=6380
```

### Custom Field Configuration

```python
from envschema import EnvSchema, Field

class Settings(EnvSchema):
    # Custom environment variable name
    api_key: str = Field(env="SECRET_API_KEY")
    
    # With description for documentation
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    
    # Custom prefix for nested schema
    db: DatabaseConfig = Field(
        prefix="DB_",
        description="Database configuration"
    )
```

### Validation and Error Handling

```python
from envschema import EnvSchema, EnvSchemaError

class Settings(EnvSchema):
    port: int
    debug: bool

try:
    settings = Settings.load()
except EnvSchemaError as e:
    # Get detailed error information
    print(e)
    
    # Access individual errors
    for error in e.errors:
        print(f"Field: {error.field_name}")
        print(f"Env var: {error.env_var}")
        print(f"Message: {error.message}")
```

**Example error output:**

```
Failed to load environment variables (2 errors):
  * PORT: missing required environment variable (expected type: int)
  * DEBUG: invalid boolean value 'maybe' (expected: true/false/yes/no/1/0/on/off) (expected type: bool) [got: 'maybe']
```

## 📖 Documentation Generation

### Generate `.env.example`

```python
from envschema.docs import DocumentationGenerator

class Settings(EnvSchema):
    api_key: str = Field(description="API key for external service")
    debug: bool = False
    port: int = Field(default=8000, description="Server port")

# Generate .env.example file
generator = DocumentationGenerator(Settings)
generator.generate_example_env(".env.example")
```

**Generated `.env.example`:**

```bash
# API key for external service required
API_KEY=your_value_here

# default: false
DEBUG=false

# Server port default: 8000
PORT=8000
```

### Generate Markdown Documentation

```python
# Generate markdown documentation
docs = generator.generate_markdown_docs()
print(docs)

# Or save to file
with open("ENV_VARS.md", "w") as f:
    f.write(docs)
```

**Generated documentation includes:**

- Overview table with all variables
- Types and requirements
- Default values
- Descriptions
- Usage examples

## 🔧 Advanced Features

### Custom Type Casters

```python
from datetime import timedelta
from envschema.casters import register_caster

def cast_timedelta(value: str) -> timedelta:
    """Cast string to timedelta (expects seconds)."""
    return timedelta(seconds=int(value))

# Register custom caster
register_caster(timedelta, cast_timedelta)

class Settings(EnvSchema):
    timeout: timedelta = timedelta(seconds=30)
```

### Working with Prefixes

```python
class Settings(EnvSchema):
    api_key: str

# Load with global prefix
settings = Settings.load(prefix="MYAPP_")
# Expects: MYAPP_API_KEY
```

### Load from Custom Dict

```python
# Load from custom dictionary (useful for testing)
custom_env = {
    "API_KEY": "test-key",
    "DEBUG": "true"
}

settings = Settings.load(env=custom_env)
```

## 🧪 Testing

```python
import pytest
from envschema import EnvSchema, EnvSchemaError

def test_settings_validation():
    """Test settings validation."""
    test_env = {
        "API_KEY": "test-key",
        "PORT": "8000"
    }
    
    settings = Settings.load(env=test_env)
    
    assert settings.api_key == "test-key"
    assert settings.port == 8000

def test_missing_required_field():
    """Test missing required field raises error."""
    with pytest.raises(EnvSchemaError) as exc_info:
        Settings.load(env={})
    
    assert "missing required environment variable" in str(exc_info.value)
```

## 📋 Best Practices

1. **Use type hints**: Always specify types for better validation
2. **Add descriptions**: Help your team understand configuration options
3. **Group related settings**: Use nested schemas for logical grouping
4. **Generate documentation**: Keep `.env.example` and docs up-to-date
5. **Validate early**: Load settings at application startup
6. **Use `.env` for development**: Keep production secrets secure

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

---

<div align="center">
Made with ❤️
</div>
