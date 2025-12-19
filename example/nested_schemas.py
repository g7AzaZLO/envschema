from envschema import EnvSchema, Field


class DatabaseSettings(EnvSchema):
    """Database settings."""

    host: str
    port: int = 5432
    user: str
    password: str


class Settings(EnvSchema):
    """Main application schema."""

    debug: bool = False
    db: DatabaseSettings = Field(prefix="DB_")


if __name__ == "__main__":
    settings = Settings.load()
    print(settings)
    print(settings.db.host)
