---
name: Backend Python
description: Apply Python tooling standards including uv package management, pytest testing, ruff/mypy code quality, one-line docstrings, and self-documenting code practices. Use this skill when working with Python backend code, managing dependencies, running tests, or ensuring code quality. Apply when installing packages, writing tests, formatting code, type checking, adding docstrings, organizing imports, or deciding whether to create new files vs. extending existing ones. Use for any Python development task requiring adherence to tooling standards and best practices.
---

# Backend Python

## When to use this skill

- When installing or managing Python packages and dependencies
- When writing or running unit tests, integration tests, or test suites
- When formatting Python code or fixing linting issues
- When adding type hints or running type checking
- When writing function/method docstrings
- When organizing imports in Python files
- When deciding whether to create a new Python file or extend existing ones
- When setting up code quality checks (linting, formatting, type checking)
- When running coverage reports or analyzing test results
- When ensuring code follows Python best practices and tooling standards

This Skill provides Claude Code with specific guidance on how to adhere to Python tooling standards and best practices for backend development.

## Instructions

### Package Management - uv Only

**ALWAYS use `uv` for Python package operations. NEVER use `pip` directly.**

```bash
uv pip install package-name
uv pip install -r requirements.txt
uv pip list
uv pip show package-name
```

**Why uv:** Faster resolution, better dependency management, project standard, consistent across environments

### Testing with pytest

```bash
uv run pytest                              # All tests
uv run pytest -m unit                      # Unit tests only
uv run pytest -m integration               # Integration tests only
uv run pytest tests/unit/test_module.py   # Specific file
uv run pytest --cov=src --cov-report=term-missing  # With coverage
```

### Code Quality Tools

**Ruff (Linting & Formatting):**
```bash
ruff check . --fix      # Auto-fix issues
ruff format .           # Format all code
```

**Mypy (Type Checking):**
```bash
mypy src --strict       # Strict type checking
```

**Basedpyright (Alternative Type Checker):**
```bash
basedpyright src        # Type checking with basedpyright
```

### Docstring Style

**Use one-line docstrings for functions and methods.**

Keep them concise - just describe what the function does, not how.

Multi-line docstrings acceptable for complex functions, but prefer one-liners.

### Comments

**Write self-documenting code. Avoid inline comments.**

Use clear variable and function names instead of comments.

Use comments only for:
- Complex algorithms requiring explanation
- Non-obvious business logic
- Workarounds for external library bugs

### File Operations

**Prefer editing existing files over creating new ones.**

Before creating a new file, ask:
- Can this fit in an existing module?
- Is there a related file to extend?
- Does this need to be separate?

Benefits: Reduces bloat, maintains coherent structure, easier navigation.

### Import Organization

**Order:** Standard library → Third-party → Local imports

Separate each group with a blank line.

Tools like `ruff` automatically organize imports.
