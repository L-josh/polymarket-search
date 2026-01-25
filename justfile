# List available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Format code
fmt:
    uv run black src/ tests/
    uv run ruff check --fix src/ tests/

# Type check
types:
    uv run mypy src/

# Run tests
test:
    uv run pytest -v

# Run all checks
check: fmt types test

# Run the CLI
run *ARGS:
    uv run polymarket {{ARGS}}