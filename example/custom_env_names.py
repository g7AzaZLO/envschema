from envschema import EnvSchema, Field


class Settings(EnvSchema):
    """Example with custom environment variable names."""

    database_url: str = Field(env="DATABASE_URL")
    secret_key: str = Field(env="SECRET_KEY")
    timeout: int = Field(default=30, env="APP_TIMEOUT")


if __name__ == "__main__":
    settings = Settings.load()
    print(settings)
