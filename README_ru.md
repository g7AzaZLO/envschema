# EnvSchema

<div align="center">

![PyPI - Version](https://img.shields.io/pypi/v/envschema?color=blue)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/envschema)
![License](https://img.shields.io/github/license/g7azazlo/envschema)

**Типобезопасные переменные окружения с автоматической валидацией и генерацией документации**

[Документация](#документация) | [Установка](#установка) | [Быстрый старт](#быстрый-старт) | [Примеры](#примеры) | [Read in English](README.md)

</div>

---

## 🎯 Описание

**EnvSchema** — это легковесная Python библиотека для управления переменными окружения с автоматической валидацией типов, поддержкой вложенных схем и встроенной генерацией документации. Она устраняет шаблонный код и обеспечивает типобезопасность конфигурации вашего приложения.

## ✨ Основные возможности

- 🔒 **Типобезопасность**: Полная поддержка типизации с автоматической валидацией
- 🎨 **Чистый синтаксис**: Pythonic API с определениями в стиле dataclass
- 🏗️ **Вложенные схемы**: Поддержка сложных иерархических конфигураций
- 📝 **Автодокументация**: Автоматическая генерация `.env.example` и Markdown документации
- 🔄 **Гибкие типы**: Поддержка `str`, `int`, `float`, `bool`, `list`, `dict`, `Optional`
- 🌐 **Поддержка `.env`**: Загрузка переменных из `.env` файлов (требуется `python-dotenv`)
- ⚡ **Без зависимостей**: Базовая функциональность работает без внешних пакетов
- 🎯 **Понятные ошибки**: Детальные сообщения об ошибках валидации

## 📦 Установка

```bash
# Базовая установка
pip install envschema

# С поддержкой .env файлов
pip install envschema[dotenv]
# или
pip install envschema python-dotenv
```

## 🚀 Быстрый старт

### Базовый пример

```python
from envschema import EnvSchema, Field

class Settings(EnvSchema):
    # Обязательные поля
    api_key: str
    database_url: str
    
    # Опциональные поля со значениями по умолчанию
    debug: bool = False
    port: int = 8000
    
    # Поле с кастомным именем переменной и описанием
    secret: str = Field(
        env="SECRET_KEY",
        description="Секретный ключ для шифрования"
    )
    
    # Опциональное поле
    redis_url: str | None = None

# Загрузка из переменных окружения
settings = Settings.load()

# Доступ к значениям
print(settings.api_key)
print(settings.port)
```

### Работа с `.env` файлом

```python
# Загрузка из .env файла
settings = Settings.load(dotenv_path=".env")

# Автопоиск .env файла в текущей или родительских директориях
settings = Settings.load(dotenv_path=True)

# Перезапись системных переменных значениями из .env
settings = Settings.load(dotenv_path=".env", dotenv_override=True)
```

## 📚 Примеры

### Поддерживаемые типы

```python
from envschema import EnvSchema

class Config(EnvSchema):
    # Строка
    name: str = "default"
    
    # Целое число
    workers: int = 4
    
    # Число с плавающей точкой
    timeout: float = 30.5
    
    # Булево значение (принимает: true/false, yes/no, 1/0, on/off)
    enabled: bool = True
    
    # Список (через запятую или JSON массив)
    hosts: list[str] = ["localhost"]
    allowed_ids: list[int] = [1, 2, 3]
    
    # Словарь (JSON объект)
    metadata: dict = {"version": "1.0"}
    
    # Опциональное значение
    optional_value: str | None = None
```

**Переменные окружения:**

```bash
NAME=myapp
WORKERS=8
TIMEOUT=60.0
ENABLED=true
HOSTS=host1,host2,host3
ALLOWED_IDS=[10, 20, 30]
METADATA={"key": "value"}
```

### Вложенные схемы

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
    # Вложенные схемы с автоматическим префиксом
    database: DatabaseConfig
    redis: RedisConfig
    
    # Вложенная схема с кастомным префиксом
    cache: RedisConfig = Field(prefix="CACHE_")

# Загрузка конфигурации
settings = Settings.load()

# Доступ к вложенным значениям
print(settings.database.host)
print(settings.redis.port)
```

**Переменные окружения:**

```bash
# Конфигурация базы данных (префикс: DATABASE_)
DATABASE_HOST=db.example.com
DATABASE_PORT=5432
DATABASE_NAME=mydb
DATABASE_USER=admin
DATABASE_PASSWORD=secret123

# Конфигурация Redis (префикс: REDIS_)
REDIS_HOST=redis.example.com
REDIS_PORT=6379

# Конфигурация кеша (кастомный префикс: CACHE_)
CACHE_HOST=cache.example.com
CACHE_PORT=6380
```

### Настройка полей

```python
from envschema import EnvSchema, Field

class Settings(EnvSchema):
    # Кастомное имя переменной окружения
    api_key: str = Field(env="SECRET_API_KEY")
    
    # С описанием для документации
    max_retries: int = Field(
        default=3,
        description="Максимальное количество попыток повтора"
    )
    
    # Кастомный префикс для вложенной схемы
    db: DatabaseConfig = Field(
        prefix="DB_",
        description="Конфигурация базы данных"
    )
```

### Валидация и обработка ошибок

```python
from envschema import EnvSchema, EnvSchemaError

class Settings(EnvSchema):
    port: int
    debug: bool

try:
    settings = Settings.load()
except EnvSchemaError as e:
    # Получение детальной информации об ошибке
    print(e)
    
    # Доступ к отдельным ошибкам
    for error in e.errors:
        print(f"Поле: {error.field_name}")
        print(f"Переменная: {error.env_var}")
        print(f"Сообщение: {error.message}")
```

**Пример вывода ошибки:**

```
Failed to load environment variables (2 errors):
  * PORT: missing required environment variable (expected type: int)
  * DEBUG: invalid boolean value 'maybe' (expected: true/false/yes/no/1/0/on/off) (expected type: bool) [got: 'maybe']
```

## 📖 Генерация документации

### Генерация `.env.example`

```python
from envschema.docs import DocumentationGenerator

class Settings(EnvSchema):
    api_key: str = Field(description="API ключ для внешнего сервиса")
    debug: bool = False
    port: int = Field(default=8000, description="Порт сервера")

# Генерация .env.example файла
generator = DocumentationGenerator(Settings)
generator.generate_example_env(".env.example")
```

**Сгенерированный `.env.example`:**

```bash
# API ключ для внешнего сервиса required
API_KEY=your_value_here

# default: false
DEBUG=false

# Порт сервера default: 8000
PORT=8000
```

### Генерация Markdown документации

```python
# Генерация markdown документации
docs = generator.generate_markdown_docs()
print(docs)

# Или сохранение в файл
with open("ENV_VARS.md", "w") as f:
    f.write(docs)
```

**Сгенерированная документация включает:**

- Таблицу со всеми переменными
- Типы и требования
- Значения по умолчанию
- Описания
- Примеры использования

## 🔧 Продвинутые возможности

### Кастомные преобразователи типов

```python
from datetime import timedelta
from envschema.casters import register_caster

def cast_timedelta(value: str) -> timedelta:
    """Преобразование строки в timedelta (ожидается количество секунд)."""
    return timedelta(seconds=int(value))

# Регистрация кастомного преобразователя
register_caster(timedelta, cast_timedelta)

class Settings(EnvSchema):
    timeout: timedelta = timedelta(seconds=30)
```

### Работа с префиксами

```python
class Settings(EnvSchema):
    api_key: str

# Загрузка с глобальным префиксом
settings = Settings.load(prefix="MYAPP_")
# Ожидается: MYAPP_API_KEY
```

### Загрузка из кастомного словаря

```python
# Загрузка из кастомного словаря (полезно для тестирования)
custom_env = {
    "API_KEY": "test-key",
    "DEBUG": "true"
}

settings = Settings.load(env=custom_env)
```

## 🧪 Тестирование

```python
import pytest
from envschema import EnvSchema, EnvSchemaError

def test_settings_validation():
    """Тест валидации настроек."""
    test_env = {
        "API_KEY": "test-key",
        "PORT": "8000"
    }
    
    settings = Settings.load(env=test_env)
    
    assert settings.api_key == "test-key"
    assert settings.port == 8000

def test_missing_required_field():
    """Тест отсутствия обязательного поля вызывает ошибку."""
    with pytest.raises(EnvSchemaError) as exc_info:
        Settings.load(env={})
    
    assert "missing required environment variable" in str(exc_info.value)
```

## 📋 Лучшие практики

1. **Используйте аннотации типов**: Всегда указывайте типы для лучшей валидации
2. **Добавляйте описания**: Помогите команде понять параметры конфигурации
3. **Группируйте связанные настройки**: Используйте вложенные схемы для логической группировки
4. **Генерируйте документацию**: Держите `.env.example` и документацию актуальными
5. **Валидируйте рано**: Загружайте настройки при старте приложения
6. **Используйте `.env` для разработки**: Храните production секреты в безопасности

## 🤝 Участие в разработке

Мы приветствуем ваш вклад! Пожалуйста, не стесняйтесь отправлять Pull Request.

## 📄 Лицензия

Проект распространяется под лицензией Apache 2.0 - см. файл LICENSE для деталей.


---

<div align="center">
Сделано с ❤️
</div>
