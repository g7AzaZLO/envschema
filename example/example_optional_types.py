"""Examples of Optional types usage."""

from envschema import EnvSchema, Field


def example_basic_optional() -> None:
    """Basic example of Optional usage."""
    print("=== Example 1: Basic Optional usage ===\n")

    class Settings(EnvSchema):
        database_url: str

        api_key: str | None
        cache_url: str | None
        redis_url: str | None

    env = {"DATABASE_URL": "postgres://localhost/mydb"}

    settings = Settings.load(env=env)

    print(f"Database URL: {settings.database_url}")
    print(f"API Key: {settings.api_key}")
    print(f"Cache URL: {settings.cache_url}")
    print(f"Redis URL: {settings.redis_url}")


def example_optional_with_values() -> None:
    """Example of Optional fields with provided values."""
    print("\n=== Example 2: Optional with values ===\n")

    class Settings(EnvSchema):
        database_url: str
        api_key: str | None
        cache_ttl: int | None
        debug: bool | None

    env = {
        "DATABASE_URL": "postgres://localhost/mydb",
        "API_KEY": "secret_api_key_123",
        "CACHE_TTL": "3600",
        "DEBUG": "true",
    }

    settings = Settings.load(env=env)

    print(f"Database URL: {settings.database_url}")
    print(f"API Key: {settings.api_key}")
    print(f"Cache TTL: {settings.cache_ttl}")
    print(f"Debug: {settings.debug}")


def example_optional_vs_default() -> None:
    """Example of difference between Optional and default values."""
    print("\n=== Example 3: Optional vs Default ===\n")

    class Settings(EnvSchema):
        api_key: str | None

        timeout: int = 30

        retry_count: int | None = 3

    env = {}

    settings = Settings.load(env=env)

    print(f"API Key (Optional): {settings.api_key}")
    print(f"Timeout (Default): {settings.timeout}")
    print(f"Retry Count (Optional + Default): {settings.retry_count}")

    print("\nSemantics:")
    print("- Optional[str]: 'may be absent'")
    print("- str with default: 'always has value'")
    print("- Optional[int] = 3: 'may be overridden, otherwise 3'")


def example_real_world_config() -> None:
    """Real-world application configuration example."""
    print("\n=== Example 4: Real-world configuration ===\n")

    class Settings(EnvSchema):
        app_name: str
        database_url: str
        secret_key: str

        sentry_dsn: str | None = Field(description="Sentry DSN for error tracking")
        slack_webhook: str | None = Field(description="Slack webhook for notifications")
        datadog_api_key: str | None = Field(description="Datadog API key for metrics")

        log_level: str = "INFO"
        workers: int = 4
        debug: bool = False

        enable_cache: bool | None = Field(description="Enable Redis caching")
        cache_ttl: int | None = Field(description="Cache TTL in seconds")

    env = {
        "APP_NAME": "MyApp",
        "DATABASE_URL": "postgres://localhost/myapp",
        "SECRET_KEY": "super-secret-key",
        "SENTRY_DSN": "https://sentry.io/project/123",
        "LOG_LEVEL": "DEBUG",
        "ENABLE_CACHE": "true",
    }

    settings = Settings.load(env=env)

    print(f"App Name: {settings.app_name}")
    print(f"Database: {settings.database_url}")
    print(f"Log Level: {settings.log_level}")
    print("\nIntegrations:")
    print(f"  Sentry: {settings.sentry_dsn}")
    print(f"  Slack: {settings.slack_webhook or 'Not configured'}")
    print(f"  Datadog: {settings.datadog_api_key or 'Not configured'}")
    print("\nCaching:")
    print(f"  Enabled: {settings.enable_cache}")
    print(f"  TTL: {settings.cache_ttl or 'Default'}")


def example_optional_third_party_services() -> None:
    """Example of configuring optional third-party services."""
    print("\n=== Example 5: Optional services ===\n")

    class EmailSettings(EnvSchema):
        smtp_host: str
        smtp_port: int = 587
        username: str
        password: str
        from_email: str

    class S3Settings(EnvSchema):
        bucket: str
        region: str = "us-east-1"
        access_key: str
        secret_key: str

    class Settings(EnvSchema):
        app_name: str

        email_enabled: bool | None
        email: EmailSettings | None = Field(prefix="EMAIL_")

        s3_enabled: bool | None
        s3: S3Settings | None = Field(prefix="S3_")

    prod_env = {
        "APP_NAME": "MyApp",
        "EMAIL_ENABLED": "true",
        "EMAIL_SMTP_HOST": "smtp.gmail.com",
        "EMAIL_USERNAME": "app@example.com",
        "EMAIL_PASSWORD": "password",
        "EMAIL_FROM_EMAIL": "noreply@example.com",
        "S3_ENABLED": "true",
        "S3_BUCKET": "my-bucket",
        "S3_ACCESS_KEY": "key",
        "S3_SECRET_KEY": "secret",
    }

    dev_env = {"APP_NAME": "MyApp-Dev"}

    print("Production settings:")
    prod_settings = Settings.load(env=prod_env)
    print(f"  Email enabled: {prod_settings.email_enabled}")
    print(f"  S3 enabled: {prod_settings.s3_enabled}")

    print("\nDevelopment settings:")
    dev_settings = Settings.load(env=dev_env)
    print(f"  Email enabled: {dev_settings.email_enabled}")
    print(f"  S3 enabled: {dev_settings.s3_enabled}")
    print("  (using mocks/local services)")


def example_optional_type_hints() -> None:
    """Example of using different Optional syntaxes."""
    print("\n=== Example 6: Optional syntax ===\n")

    class Settings(EnvSchema):
        field1: str | None
        field2: str | None
        field3: str | None

    env = {}

    settings = Settings.load(env=env)

    print(f"field1 (Optional[str]): {settings.field1}")
    print(f"field2 (Union[str, None]): {settings.field2}")
    print(f"field3 (str | None): {settings.field3}")
    print("\nAll three fields return None")


def example_optional_validation() -> None:
    """Example of Optional fields validation."""
    print("\n=== Example 7: Optional validation ===\n")

    from envschema import EnvSchemaError

    class Settings(EnvSchema):
        port: int | None
        timeout: float | None
        debug: bool | None

    valid_env = {
        "PORT": "8080",
        "TIMEOUT": "30.5",
        "DEBUG": "true",
    }

    settings = Settings.load(env=valid_env)
    print("Valid values:")
    print(f"  Port: {settings.port}")
    print(f"  Timeout: {settings.timeout}")
    print(f"  Debug: {settings.debug}")

    invalid_env = {
        "PORT": "not_a_number",
        "TIMEOUT": "not_a_float",
    }

    print("\nInvalid values:")
    try:
        Settings.load(env=invalid_env)
    except EnvSchemaError as e:
        print(f"  Found errors: {len(e.errors)}")
        for error in e.errors:
            print(f"    • {error.env_var}: {error.message}")


def example_migration_guide() -> None:
    """Example of migrating to Optional types."""
    print("\n=== Example 8: Migration to Optional ===\n")

    class OldSettings(EnvSchema):
        api_key: str = Field(default=None)  # type: ignore
        timeout: int = Field(default=None)  # type: ignore

    class NewSettings(EnvSchema):
        api_key: str | None
        timeout: int | None

    print("Old style:")
    print("  api_key: str = Field(default=None)")
    print("  ❌ Contradicts type (str cannot be None)")
    print("  ❌ Requires type: ignore")

    print("\nNew style:")
    print("  api_key: Optional[str]")
    print("  ✅ Semantically correct")
    print("  ✅ IDE and mypy understand type")
    print("  ✅ Explicitly shows intention")


if __name__ == "__main__":
    example_basic_optional()
    example_optional_with_values()
    example_optional_vs_default()
    example_real_world_config()
    example_optional_third_party_services()
    example_optional_type_hints()
    example_optional_validation()
    example_migration_guide()
