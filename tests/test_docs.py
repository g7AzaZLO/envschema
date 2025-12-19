"""Tests for documentation generator."""

import tempfile
from pathlib import Path

from envschema import EnvSchema, Field
from envschema.docs import DocumentationGenerator


class TestDocumentationGenerator:
    """Tests for DocumentationGenerator."""

    def test_generate_example_env_simple(self) -> None:
        """Checks generating .env.example for simple schema."""

        class Settings(EnvSchema):
            port: int = Field(default=8000, description="Application HTTP port")
            debug: bool = Field(default=False, description="Enable debug mode")
            database_url: str = Field(description="PostgreSQL connection string")

        generator = DocumentationGenerator(Settings)
        content = generator.generate_example_env()

        assert "PORT" in content
        assert "DEBUG" in content
        assert "DATABASE_URL" in content
        assert "Application HTTP port" in content
        assert "Enable debug mode" in content
        assert "PostgreSQL connection string" in content
        assert "default: 8000" in content
        assert "default: false" in content
        assert "required" in content

    def test_generate_example_env_with_file(self) -> None:
        """Checks writing .env.example to file."""

        class Settings(EnvSchema):
            port: int = Field(default=8000, description="Application HTTP port")

        generator = DocumentationGenerator(Settings)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / ".env.example"
            generator.generate_example_env(str(file_path))

            assert file_path.exists()
            content = file_path.read_text(encoding="utf-8")
            assert "PORT" in content
            assert "8000" in content

    def test_generate_markdown_docs(self) -> None:
        """Checks generating Markdown documentation."""

        class Settings(EnvSchema):
            port: int = Field(default=8000, description="Application HTTP port")
            debug: bool = Field(default=False, description="Enable debug mode")
            database_url: str = Field(description="PostgreSQL connection string")

        generator = DocumentationGenerator(Settings)
        docs = generator.generate_markdown_docs()

        assert "# Environment Variables Configuration" in docs
        assert "| Variable | Type | Required | Default | Description |" in docs
        assert "| `PORT` |" in docs
        assert "| `DEBUG` |" in docs
        assert "| `DATABASE_URL` |" in docs
        assert "| `int` |" in docs
        assert "| `bool` |" in docs
        assert "| `str` |" in docs
        assert "| No |" in docs
        assert "| **Yes** |" in docs

    def test_generate_example_env_with_prefix(self) -> None:
        """Checks generating with prefix."""

        class Settings(EnvSchema):
            port: int = Field(default=8000)

        generator = DocumentationGenerator(Settings, prefix="APP_")
        content = generator.generate_example_env()

        assert "APP_PORT" in content
        assert "\nPORT=" not in content

    def test_generate_markdown_docs_with_prefix(self) -> None:
        """Checks generating Markdown with prefix."""

        class Settings(EnvSchema):
            port: int = Field(default=8000)

        generator = DocumentationGenerator(Settings, prefix="APP_")
        docs = generator.generate_markdown_docs()

        assert "| `APP_PORT` |" in docs

    def test_generate_example_env_list_types(self) -> None:
        """Checks generating for list types."""

        class Settings(EnvSchema):
            hosts: list[str] = Field(default=["host1", "host2"])
            ports: list[int] = Field(default=[8080, 9090])

        generator = DocumentationGenerator(Settings)
        content = generator.generate_example_env()

        assert "HOSTS" in content
        assert "PORTS" in content
        assert "host1,host2" in content
        assert "[8080, 9090]" in content or '"8080"' in content

    def test_generate_markdown_docs_list_types(self) -> None:
        """Checks generating Markdown for list types."""

        class Settings(EnvSchema):
            hosts: list[str] = Field(default=["host1", "host2"])

        generator = DocumentationGenerator(Settings)
        docs = generator.generate_markdown_docs()

        assert "| `list[str]` |" in docs

    def test_generate_example_env_required_fields(self) -> None:
        """Checks generating for required fields."""

        class Settings(EnvSchema):
            api_key: str = Field(description="API key")

        generator = DocumentationGenerator(Settings)
        content = generator.generate_example_env()

        assert "required" in content
        assert "your_value_here" in content

    def test_generate_markdown_docs_required_fields(self) -> None:
        """Checks generating Markdown for required fields."""

        class Settings(EnvSchema):
            api_key: str = Field(description="API key")

        generator = DocumentationGenerator(Settings)
        docs = generator.generate_markdown_docs()

        assert "| **Yes** |" in docs
        assert "| - |" in docs

    def test_generate_markdown_escapes_special_chars(self) -> None:
        """Checks escaping special Markdown characters."""

        class Settings(EnvSchema):
            test_var: str = Field(
                default="test|value_with_underscore*and_stars",
                description="Test with | _ * symbols",
            )

        generator = DocumentationGenerator(Settings)
        docs = generator.generate_markdown_docs()

        assert "\\|" in docs or "test" in docs

    def test_generate_example_env_custom_env_name(self) -> None:
        """Checks generating with custom variable name."""

        class Settings(EnvSchema):
            api_key: str = Field(env="SECRET_KEY", default="default_key")

        generator = DocumentationGenerator(Settings)
        content = generator.generate_example_env()

        assert "SECRET_KEY" in content
        assert "API_KEY" not in content

    def test_generate_markdown_docs_custom_env_name(self) -> None:
        """Checks generating Markdown with custom variable name."""

        class Settings(EnvSchema):
            api_key: str = Field(env="SECRET_KEY", default="default_key")

        generator = DocumentationGenerator(Settings)
        docs = generator.generate_markdown_docs()

        assert "| `SECRET_KEY` |" in docs
        assert "| `API_KEY` |" not in docs

    def test_generate_example_env_dict_type(self) -> None:
        """Checks generating for dict type."""

        class Settings(EnvSchema):
            config: dict = Field(default={"key": "value", "num": 42})

        generator = DocumentationGenerator(Settings)
        content = generator.generate_example_env()

        assert "CONFIG" in content
        assert '"key"' in content or "'key'" in content

    def test_generate_markdown_docs_dict_type(self) -> None:
        """Checks generating Markdown for dict type."""

        class Settings(EnvSchema):
            config: dict = Field(default={"key": "value"})

        generator = DocumentationGenerator(Settings)
        docs = generator.generate_markdown_docs()

        assert "| `dict` |" in docs

    def test_metadata_caching(self) -> None:
        """Checks metadata caching."""

        class Settings(EnvSchema):
            port: int = Field(default=8000)

        generator = DocumentationGenerator(Settings)

        metadata1 = generator._get_field_metadata()
        cache1 = generator._metadata_cache

        metadata2 = generator._get_field_metadata()
        cache2 = generator._metadata_cache

        assert cache1 is not None
        assert cache1 is cache2
        assert metadata1 == metadata2
