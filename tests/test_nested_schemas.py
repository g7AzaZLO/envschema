import pytest

from envschema import EnvSchema, EnvSchemaError, Field


class DatabaseSettings(EnvSchema):
    """Database settings."""

    host: str = "localhost"
    port: int = 5432
    name: str
    user: str = Field(default="admin", description="Database user")


class RedisSettings(EnvSchema):
    """Redis settings."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0


class S3Settings(EnvSchema):
    """S3 settings."""

    bucket: str
    region: str = "us-east-1"
    endpoint: str | None = Field(default=None, description="Custom S3 endpoint")


def test_nested_schema_basic() -> None:
    """Test basic nested schema loading."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")
        app_name: str

    env = {
        "DB_HOST": "postgres.local",
        "DB_PORT": "5433",
        "DB_NAME": "myapp",
        "DB_USER": "admin",
        "APP_NAME": "MyApp",
    }

    settings = Settings.load(env=env)

    assert settings.app_name == "MyApp"
    assert isinstance(settings.db, DatabaseSettings)
    assert settings.db.host == "postgres.local"
    assert settings.db.port == 5433
    assert settings.db.name == "myapp"
    assert settings.db.user == "admin"


def test_nested_schema_default_prefix() -> None:
    """Test automatic prefix (FIELD_NAME_)."""

    class Settings(EnvSchema):
        redis: RedisSettings
        app_name: str

    env = {
        "REDIS_HOST": "redis.local",
        "REDIS_PORT": "6380",
        "REDIS_DB": "1",
        "APP_NAME": "MyApp",
    }

    settings = Settings.load(env=env)

    assert settings.app_name == "MyApp"
    assert settings.redis.host == "redis.local"
    assert settings.redis.port == 6380
    assert settings.redis.db == 1


def test_nested_schema_multiple_nested() -> None:
    """Test multiple nested schemas."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")
        redis: RedisSettings = Field(prefix="REDIS_")
        s3: S3Settings = Field(prefix="S3_")

    env = {
        "DB_HOST": "postgres.local",
        "DB_PORT": "5432",
        "DB_NAME": "myapp",
        "DB_USER": "admin",
        "REDIS_HOST": "redis.local",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0",
        "S3_BUCKET": "my-bucket",
        "S3_REGION": "eu-west-1",
    }

    settings = Settings.load(env=env)

    assert settings.db.host == "postgres.local"
    assert settings.db.name == "myapp"
    assert settings.redis.host == "redis.local"
    assert settings.redis.db == 0
    assert settings.s3.bucket == "my-bucket"
    assert settings.s3.region == "eu-west-1"
    assert settings.s3.endpoint is None


def test_nested_schema_with_defaults() -> None:
    """Test default values in nested schemas."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")

    env = {
        "DB_NAME": "myapp",
    }

    settings = Settings.load(env=env)

    assert settings.db.host == "localhost"
    assert settings.db.port == 5432
    assert settings.db.name == "myapp"
    assert settings.db.user == "admin"


def test_nested_schema_missing_required_field() -> None:
    """Test missing required field in nested schema."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")

    env = {
        "DB_HOST": "postgres.local",
    }

    with pytest.raises(EnvSchemaError) as exc_info:
        Settings.load(env=env)

    error = exc_info.value
    assert len(error.errors) == 1
    env_vars = {e.env_var for e in error.errors}
    assert "DB_NAME" in env_vars
    assert any("missing required" in e.message for e in error.errors)


def test_nested_schema_multiple_errors() -> None:
    """Test error aggregation from nested schemas."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")
        redis: RedisSettings = Field(prefix="REDIS_")

    env = {
        "DB_PORT": "invalid_port",
        "REDIS_PORT": "invalid_port",
    }

    with pytest.raises(EnvSchemaError) as exc_info:
        Settings.load(env=env)

    error = exc_info.value
    assert len(error.errors) >= 2

    env_vars = {e.env_var for e in error.errors}
    assert "DB_NAME" in env_vars
    assert "DB_PORT" in env_vars


def test_nested_schema_deep_nesting() -> None:
    """Test deep schema nesting."""

    class InnerSettings(EnvSchema):
        value: str

    class MiddleSettings(EnvSchema):
        inner: InnerSettings = Field(prefix="INNER_")

    class OuterSettings(EnvSchema):
        middle: MiddleSettings = Field(prefix="MIDDLE_")

    env = {
        "MIDDLE_INNER_VALUE": "deep_value",
    }

    settings = OuterSettings.load(env=env)

    assert settings.middle.inner.value == "deep_value"


def test_nested_schema_prefix_composition() -> None:
    """Test prefix composition."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")

    env = {
        "PROD_DB_HOST": "prod.postgres.local",
        "PROD_DB_PORT": "5432",
        "PROD_DB_NAME": "prod_db",
        "PROD_DB_USER": "prod_user",
    }

    settings = Settings.load(env=env, prefix="PROD_")

    assert settings.db.host == "prod.postgres.local"
    assert settings.db.name == "prod_db"


def test_nested_schema_with_parent_prefix() -> None:
    """Test parent schema prefix."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DATABASE_")
        app_name: str

    env = {
        "APP_DATABASE_HOST": "postgres.local",
        "APP_DATABASE_PORT": "5432",
        "APP_DATABASE_NAME": "myapp",
        "APP_DATABASE_USER": "user",
        "APP_APP_NAME": "MyApp",
    }

    settings = Settings.load(env=env, prefix="APP_")

    assert settings.db.host == "postgres.local"
    assert settings.app_name == "MyApp"


def test_nested_schema_custom_env_names() -> None:
    """Test custom variable names in nested schemas."""

    class CustomDB(EnvSchema):
        host: str = Field(env="DB_HOSTNAME")
        port: int = Field(env="DB_PORT_NUMBER")
        name: str

    class Settings(EnvSchema):
        db: CustomDB = Field(prefix="")

    env = {
        "DB_HOSTNAME": "custom.postgres.local",
        "DB_PORT_NUMBER": "5433",
        "NAME": "myapp",
    }

    settings = Settings.load(env=env)

    assert settings.db.host == "custom.postgres.local"
    assert settings.db.port == 5433


def test_nested_schema_repr() -> None:
    """Test string representation of nested schemas."""

    class Settings(EnvSchema):
        db: DatabaseSettings = Field(prefix="DB_")

    env = {
        "DB_HOST": "postgres.local",
        "DB_PORT": "5432",
        "DB_NAME": "myapp",
        "DB_USER": "admin",
    }

    settings = Settings.load(env=env)

    repr_str = repr(settings)
    assert "Settings(" in repr_str
    assert "db=" in repr_str

    db_repr = repr(settings.db)
    assert "DatabaseSettings(" in db_repr
    assert "host='postgres.local'" in db_repr
    assert "name='myapp'" in db_repr


def test_nested_schema_mixed_fields() -> None:
    """Test mixed fields (regular + nested)."""

    class Settings(EnvSchema):
        app_name: str
        debug: bool = False
        db: DatabaseSettings = Field(prefix="DB_")
        redis: RedisSettings = Field(prefix="REDIS_")
        workers: int = 4

    env = {
        "APP_NAME": "MyApp",
        "DEBUG": "true",
        "DB_HOST": "postgres.local",
        "DB_PORT": "5432",
        "DB_NAME": "myapp",
        "DB_USER": "admin",
        "REDIS_HOST": "redis.local",
        "REDIS_PORT": "6379",
        "REDIS_DB": "0",
        "WORKERS": "8",
    }

    settings = Settings.load(env=env)

    assert settings.app_name == "MyApp"
    assert settings.debug is True
    assert settings.workers == 8
    assert settings.db.host == "postgres.local"
    assert settings.redis.port == 6379
