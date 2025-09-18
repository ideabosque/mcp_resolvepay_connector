# MCP ResolvePay Connector Development Plan

## Purpose
Provide an actionable view of the current connector implementation, outstanding work, and quality expectations for the MCP ResolvePay integration.

## Current Implementation Snapshot (v0.1.0)
- Connector entry point `MCPResolvepayConnector` wires authentication, rate limiting, HTTP client, and request validation.
- Supporting modules:
  - `auth.py`: Basic authentication helper that wraps merchant id and API key credentials.
  - `http_client.py`: Requests-based client with retry policy, error mapping, and token bucket throttling.
  - `models.py`: Pydantic models for configuration, customer payloads, and credit check objects.
  - `exceptions.py`: Typed hierarchy surfaced by the connector and tests.
  - `rate_limiter.py`: Token bucket limiter tuned via `rate_limit_calls_per_second`.
  - `utils.py`: Shared helpers for pagination, serialization, and logging contexts.
- Test suite under `mcp_resolvepay_connector/tests/` exercises models, auth, utilities, and connector flows with mocked responses.
- Tooling: Linting and formatting use `black`, `isort`, `flake8`, and `mypy` (strict mode). Tests run directly with pytest.

## Recently Completed
- Project bootstrapped with `pyproject.toml`, editable install, and optional `test`/`dev` extras.
- Added comprehensive unit tests with fixtures for customer and credit check scenarios.
- Implemented standardized response envelopes and error handling decorators.
- Documented contributor workflow in `AGENTS.md` and refreshed README usage instructions.

## Near-Term Roadmap
1. **Integration Hardening**
   - Validate request/response contracts against ResolvePay sandbox once credentials are available.
   - Add error translation coverage for non-200 responses (timeouts, 5xx, malformed payloads).
   - Capture rate limiter metrics and expose them through logger debug payloads when `debug_mode` is enabled.
2. **Data Model Enhancements**
   - Expand customer search filters to cover phone numbers and custom attributes once API docs confirm availability.
   - Enrich `CreditCheckResult` with limit history and decision reasons if provided by newer endpoints.
3. **Developer Experience**
   - Provide canned response fixtures and sample JSON payloads under `tests/fixtures/` for easier integration testing.
   - Offer a CLI example or notebook demonstrating the connector inside the Silva Engine MCP runtime.
4. **Release Readiness**
   - Configure automated lint/test workflows (GitHub Actions) using pytest commands.
   - Publish changelog and versioning guidelines prior to tagging v0.2.0.

## Testing & Quality Expectations
- Maintain unit and component tests for every public method; target >= 80% coverage (`pytest --cov=mcp_resolvepay_connector --cov-fail-under=80`).
- Mark slow or integration suites with `@pytest.mark.integration` for opt-in execution.
- Use `responses` or equivalent HTTP mocking for deterministic tests; real API calls should reside in gated integration tests with `.env` driven credentials.
- Enforce formatting (`black`, `isort`) and linting (`flake8`) pre-commit; treat mypy warnings as build blockers.

## Documentation & Support Tasks
- Keep `README.md` aligned with new endpoints or configuration flags.
- Update `AGENTS.md` when workflow or review expectations change.
- Capture API-specific caveats (rate limits, sandbox behavior) in a future `docs/` directory when empirical data is available.

## Risks & Mitigations
- **External API variability**: Sandbox behavior may drift from production. Mitigation: record fixtures from both environments and guard with feature flags.
- **Credential management**: Developer machines require `.env` files; ensure secrets never land in the repo by adding pre-commit checks if needed.
- **Rate limit breaches**: Current limiter assumes steady state. Monitor for burst behaviors and adjust bucket size or introduce jittered retries.

## Reference Module Map
- Customer workflows: `mcp_resolvepay_connector.py` (`create_customer`, `get_customer`, `update_customer`, `search_customers`).
- Credit checks: `mcp_resolvepay_connector.py` (`request_customer_credit_check`, `get_credit_check_status`).
- Validation helpers: `models.py`, `utils.py`.
- Errors and retry logic: `exceptions.py`, `http_client.py`, `rate_limiter.py`.

## Success Criteria for Next Release
- Integration tests pass against ResolvePay sandbox with mocked fallbacks.
- Coverage remains >= 80% with meaningful assertions for new features.
- README and AGENTS stay current; CHANGELOG captures user-facing updates.
- Packaging ready for PyPI publish (version bump, metadata review, optional build artifact verification).
