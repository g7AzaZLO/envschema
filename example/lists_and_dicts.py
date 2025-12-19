from envschema import EnvSchema


class Settings(EnvSchema):
    """Example of complex types."""

    allowed_hosts: list[str]
    retry_delays: list[int]
    feature_flags: dict


if __name__ == "__main__":
    settings = Settings.load()
    print(settings.allowed_hosts)
    print(settings.retry_delays)
    print(settings.feature_flags)
