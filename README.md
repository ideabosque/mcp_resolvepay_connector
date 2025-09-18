# MCP ResolvePay Connector

Python connector for ResolvePay credit and payment APIs designed for the Silva Engine Model Context Protocol ecosystem.

## Highlights

- Manage customer lifecycle operations (create, retrieve, update, search)
- Request and monitor credit checks with consistent response envelopes
- Enforce per-second rate limits with configurable retries and timeouts
- Provide typed models, validation, and structured logging for MCP integrations

## Project Layout

```text
mcp_resolvepay_connector/
|-- auth.py               # Basic authentication helper
|-- exceptions.py         # Connector specific exception types
|-- http_client.py        # Rate limited HTTP client with retry logic
|-- models.py             # Pydantic models and configuration schemas
|-- rate_limiter.py       # Token bucket limiter
|-- utils.py              # Shared helpers
|-- tests/
    |-- conftest.py       # Fixtures and response builders
    |-- pytest.ini        # Pytest configuration
    |-- requirements.txt  # Test only dependencies
    |-- test_auth.py
    |-- test_models.py
    |-- test_utils.py
    |-- test_mcp_resolvepay_connector.py
```

## Installation

```bash
pip install -e .
```

Install optional extras for testing or development with `pip install .[test]` or `pip install .[dev]`.

## Configuration

Create a settings dictionary or load environment variables (see `mcp_resolvepay_connector/tests/.env.example`):

```python
settings = {
    "merchant_id": "your_merchant_id",
    "api_key": "your_api_key",
    "base_url": "https://api.resolvepay.com/v5",
    "timeout": 30,
    "max_retries": 3,
    "rate_limit_calls_per_second": 10,
    "debug_mode": False,
}
```

## Quick Start

```python
import logging
from mcp_resolvepay_connector import MCPResolvepayConnector

logger = logging.getLogger("resolvepay")
connector = MCPResolvepayConnector(logger, **settings)

result = connector.create_customer(
    business_name="Acme Corporation",
    business_address="123 Main Street",
    business_city="New York",
    business_state="NY",
    business_zip="10001",
    business_country="US",
    business_ap_email="ap@acme.com",
    email="contact@acme.com",
)

if result["success"]:
    print(f"Created customer {result['customer']['id']}")
```

## MCP Tools

The connector exposes the following MCP callable functions:

- `create_customer`
- `get_customer`
- `update_customer`
- `search_customers`
- `request_customer_credit_check`
- `get_credit_check_status`
- `validate_customer_data`

## Testing

Run tests directly with pytest:

```bash
# Run all tests
pytest mcp_resolvepay_connector/tests

# Run with coverage
pytest mcp_resolvepay_connector/tests --cov=mcp_resolvepay_connector --cov-report=html --cov-report=term-missing

# Run in parallel (requires pytest-xdist)
pytest mcp_resolvepay_connector/tests -n auto
```

## Development Tooling

- Format with `black mcp_resolvepay_connector` and `isort mcp_resolvepay_connector`
- Lint with `flake8`
- Run type checks with `mypy mcp_resolvepay_connector`
- Coverage threshold is set to 80 percent via `pytest --cov`

## Contributing

See `AGENTS.md` for contributor workflow, coding standards, and review expectations.

## License

MIT License - see `LICENSE` for details.

## Support

- Issues: https://github.com/bibow/mcp_resolvepay_connector/issues
- Documentation: https://github.com/bibow/mcp_resolvepay_connector#readme
