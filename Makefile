.PHONY: ci

ci:
	ruff format --check .
	ruff check .
	mypy envschema
	pytest
EOF