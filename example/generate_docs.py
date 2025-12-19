from envschema import EnvSchema, Field
from envschema.docs import DocumentationGenerator


class Settings(EnvSchema):
    """Schema for documentation generation."""

    host: str = "localhost"
    port: int
    debug: bool = False
    api_key: str = Field(description="API key for external service")


if __name__ == "__main__":
    generator = DocumentationGenerator(Settings, prefix="APP_")

    env_example = generator.generate_example_env()
    print(env_example)

    markdown_docs = generator.generate_markdown_docs()
    print(markdown_docs)
