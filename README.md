# Grox

![Unit Tests](https://github.com/grakn/grox/actions/workflows/ci.yaml/badge.svg?branch=main)
[![PyPI Downloads](https://static.pepy.tech/badge/grox)](https://pepy.tech/projects/grox)

**Grox** is a lightweight async-ready Python library for building multi-tenant AI agents, project-scoped services with graph orchestrated LLM execution flows, structured logging, request correlation, and centralized configuration.

## ✨ Features

- Singleton `GroxContext` with thread-safe project registration
- `GroxExecutionContext` object per request/input (with `tenant_id` and `project_code`)
- Per-request correlation ID and user-scoped structured logging via `structlog`
- YAML-based config loading with Pydantic
- Clean separation between global project data and per-request logic

## 🛠️ Installation

```
pip install grox
```

## For development

Poetry
```
poetry install --extras "test"
```

PIP
```
pip3 install ".[test]"
```
