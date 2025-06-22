# Flox

**Flox** is a lightweight async-ready Python library for building multi-tenant, project-scoped services with structured logging, request correlation, and centralized configuration.

## ✨ Features

- Singleton `FloxContext` with thread-safe project registration
- `Context` object per request (with `tenant_id` and `project_code`)
- Per-request correlation ID and user-scoped structured logging via `structlog`
- YAML-based config loading with Pydantic
- Clean separation between global project data and per-request logic

## 🛠️ Installation

```
pip install flox
```

## For development

```
poetry install --extras "test"
or
pip3 install ".[test]"
```
