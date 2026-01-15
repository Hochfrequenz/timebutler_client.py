# Timebutler Client Design

## Overview

Async Python client for the Timebutler API using aiohttp. The client parses CSV responses into typed Pydantic models.

## Project Structure

```
src/
  timebutler_client/
    __init__.py              # Exports TimebutlerClient, models
    client.py                # TimebutlerClient class (aiohttp-based)
    models/
      __init__.py            # Exports all models
      absence.py             # Absence model
    py.typed                 # PEP 561 marker
unittests/
  test_absences.py           # Mock-based tests with aioresponses
```

**Package name:** `timebutler_client` (underscores everywhere - PyPI, imports, directories)

## API Details

- **Base URL:** `https://app.timebutler.com/api/v1`
- **Auth:** POST parameter `auth` with API token
- **Response format:** Semicolon-delimited CSV, UTF-8
- **Date format:** `dd/mm/yyyy` (European)

## Absence Model

```python
class Absence(BaseModel):
    """
    Represents an absence entry from Timebutler.

    Date range is inclusive: an absence from 15/05/2026 to 15/05/2026
    represents a single day off (that day is included).
    """

    # Critical fields - strictly validated
    id: int
    from_date: date = Field(description="Start date (inclusive)")
    to_date: date = Field(description="End date (inclusive)")
    employee_number: str = Field(description="Employee number with leading zeros, e.g. '00123'")

    # Good to have - relaxed validation with defaults
    user_id: int = 0
    half_day: bool = False
    morning: bool = False
    absence_type: str = ""           # "Vacation", "Sickness", "Further training", etc.
    extra_vacation: bool = False
    state: str = ""                  # "Approved", "Submitted", etc.
    substitute_state: str = ""       # "No approval required", etc.
    workdays: Decimal = Decimal("0")
    hours: Decimal = Decimal("0")
    medical_certificate: str | None = None
    comments: str | None = None
    substitute_user_id: int = 0      # 0 means no substitute
```

### Computed Properties

- `employee_number_numeric: int` - Employee number without leading zeros
- `has_substitute: bool` - True when `substitute_user_id != 0`
- `is_half_day: bool` - True if this is a half-day absence
- `is_morning_half_day: bool` - True if morning half-day
- `is_afternoon_half_day: bool` - True if afternoon half-day
- `has_comments: bool` - True when comments exist and aren't whitespace

### Validators

- `employee_number` - Regex `^\d+$`, digits only
- `from_date`, `to_date` - Strict `dd/mm/yyyy` parsing, no lenient fallback

## Client Class

```python
class TimebutlerClient(BaseModel):
    """Async client for the Timebutler API."""

    base_url: str = "https://app.timebutler.com/api/v1"
    _api_key: str = PrivateAttr()

    def __init__(self, api_key: str, base_url: str = "https://app.timebutler.com/api/v1") -> None:
        ...

    async def get_absences(self, year: int) -> list[Absence]:
        """
        Fetch absences for a given year.

        Note: Despite being named 'get_', this calls a POST endpoint
        (Timebutler API only accepts POST requests).
        """
        ...
```

- API key stored as Pydantic `PrivateAttr` (won't serialize)
- Base URL configurable with default
- Session created per-call (comment in code explains this is for simplicity; can optimize later)

## Dependencies

```toml
[project]
dependencies = [
    "aiohttp>=3.10",
    "pydantic>=2.5",
]

[project.optional-dependencies]
tests = [
    "pytest==9.0.2",
    "pytest-asyncio==0.25.0",
    "aioresponses==0.7.8",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

Version constraints ensure Python 3.11-3.14 compatibility.

## Testing

- Mock-based tests using `aioresponses`
- Mock includes realistic response headers from production API
- Compare full model lists rather than individual fields
- Verify auth token and year are sent correctly as POST data

## Implementation Checklist

- [ ] Rename `mypackage` to `timebutler_client`
- [ ] Update `pyproject.toml` with package name and dependencies
- [ ] Create `models/` subpackage with `absence.py`
- [ ] Implement `TimebutlerClient` in `client.py`
- [ ] Update `__init__.py` exports
- [ ] Write tests in `unittests/test_absences.py`
- [ ] Delete old `test_myclass.py`
- [ ] Run `pip-compile pyproject.toml -o requirements.txt`
- [ ] Uncomment publishing workflow
- [ ] Run tests and linting
