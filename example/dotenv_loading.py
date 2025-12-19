from envschema import EnvSchema


class Settings(EnvSchema):
    """Loading variables from .env file."""

    debug: bool = False
    port: int


if __name__ == "__main__":
    settings = Settings.load(dotenv_path=".env")
    print(settings)

    settings = Settings.load(dotenv_path=True)
    print(settings)
