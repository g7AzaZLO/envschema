#!/usr/bin/env python


import builtins

from setuptools import setup

version = "1.0.0"

with builtins.open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="envschema",
    version=version,
    author="AzaZLO",
    author_email="maloymeee@yandex.ru",
    description=(
        "Type-safe environment variables with automatic validation "
        "and documentation generation"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/g7AzaZLO/envschema",
    download_url=f"https://github.com/g7AzaZLO/envschema/archive/v{version}.zip",
    license="Apache License 2.0",
    packages=["envschema"],
    install_requires=[
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
