# Repository Guidelines

## Project Structure & Module Organization
Package code lives under `mcp_resolvepay_connector/` with modules such as `auth.py`, `http_client.py`, `rate_limiter.py`, `models.py`, and the primary entry point `mcp_resolvepay_connector.py`.
Tests reside in `mcp_resolvepay_connector/tests/` alongside pytest config (`pytest.ini`) and fixtures (`conftest.py`).
Metadata files (`README.md`, `pyproject.toml`) sit at the repository root.

## Build, Test, and Development Commands
- Install in editable mode: `pip install -e .`
- Install test extras: `pip install .[test]`.
- Run unit suite: `pytest mcp_resolvepay_connector/tests -m "unit or not integration"`.
- Full test run: `pytest mcp_resolvepay_connector/tests`.
- Coverage gate: `pytest mcp_resolvepay_connector/tests --cov=mcp_resolvepay_connector --cov-fail-under=80`.
- Quality checks: `black mcp_resolvepay_connector`, `isort mcp_resolvepay_connector`, `flake8`, `mypy mcp_resolvepay_connector`.

## Coding Style & Naming Conventions
Adhere to PEP 8 with Black formatting (line length 100) and isort using the Black profile.
Respect strict mypy settings (`disallow_untyped_defs = true`, etc.) and keep public APIs fully typed.
Prefer PascalCase for classes (for example `MCPResolvepayConnector`), snake_case for functions, and group exceptions under `exceptions.py`.

## Testing Guidelines
Pytest discovers files named `test_*.py`, classes `Test*`, and functions `test_*`; keep new tests consistent.
Mark tests with `unit`, `integration`, or `slow` to control selection and support CI filtering.
Run in parallel when helpful via `pytest mcp_resolvepay_connector/tests -n auto`.
Use responses-based mocks for API calls and load credentials from `.env` mirrored from `tests/.env.example` for integration checks.
Aim for >= 80% coverage and exercise new models with serialization and error-path tests.

## Commit & Pull Request Guidelines
Write imperative, scoped commit messages such as `Add ResolvePay retry backoff` and group related changes.
Reference issue identifiers when available and document validation commands in the pull request description.
Attach coverage deltas or relevant logs for behavioral changes and call out breaking API updates early.
Ensure CI passes before requesting review and provide screenshots or sample payloads for user-visible changes.

## Configuration & Security Notes
Keep secrets out of source control; copy `mcp_resolvepay_connector/tests/.env.example` to `.env` locally as needed.
Tune `rate_limit_calls_per_second`, timeouts, and retry settings per ResolvePay quotas, and prefer environment variables for credentials.
