# timebutler_client

Async Python client for the [Timebutler](https://timebutler.com) API: v1 ([official docs](https://app.timebutler.com/do?ha=api&ac=10)) and v2 ([official docs](https://app.timebutler.com/api/v2/docs)).

> [!IMPORTANT]
> This is NOT an official client by Timebutler GmbH, just a community project.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python Versions (officially) supported](https://img.shields.io/pypi/pyversions/timebutler-client.svg)
![Pypi status badge](https://img.shields.io/pypi/v/timebutler-client)
![Unittests status badge](https://github.com/Hochfrequenz/timebutler_client.py/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/timebutler_client.py/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/timebutler_client.py/workflows/Linting/badge.svg)
![Formatting status badge](https://github.com/Hochfrequenz/timebutler_client.py/workflows/Formatting/badge.svg)

## Installation

```bash
pip install timebutler-client
```

## Usage

The client speaks both Timebutler APIs. v1 uses a company-wide API key and returns company-wide exports;
v2 uses a personal token and acts as the user who owns it (see [API v2](#api-v2-personal-tokens) below).

```python
from timebutler_client import TimebutlerClient

# Create client with your API key (v1)
client = TimebutlerClient(api_key="your-api-key")

# Fetch absences for a specific year
absences = await client.get_absences(year=2026)

for absence in absences:
    print(f"{absence.employee_number}: {absence.from_date} - {absence.to_date} ({absence.absence_type})")
```

## Features

> [!NOTE]
> For API v1 we only implemented a subset of the endpoints, because the API is not very convenient to develop against (no OpenAPI, no sandbox or test system, only admin API keys).

- Async HTTP client using `aiohttp`
- Typed responses using Pydantic models
- Strict date parsing (European `dd/mm/yyyy` format)
- Employee number handling with leading zeros preserved

### Supported Endpoints

| Method | Description |
|--------|-------------|
| `get_absences(year)` | Fetch absences for a given year |
| `get_projects()` | Fetch all projects |
| `get_services()` | Fetch all services |
| `get_users()` | Fetch all users |
| `get_workdays()` | Fetch workday schedules for all users (see note below) |
| `get_worktime(year?, month?, user_id?)` | Fetch worktime entries with optional filters |

> [!NOTE]
> `get_workdays()` returns a `WorkdaysResult` with two named fields: `schedules` and `invalid_employees`.
> `invalid_employees` contains users whose `employee_number` field in Timebutler is empty or non-numeric.
> This is expected — it occurs for DC users on test systems and for new employees who are not yet fully
> set up in production. Because employee numbers are mandatory for downstream processing, these users are
> filtered out here rather than propagating incomplete data further along the pipeline.

### Example: Tracking Time by Project

```python
from timebutler_client import TimebutlerClient

client = TimebutlerClient(api_key="your-api-key")

# Get all projects and worktime entries
projects = await client.get_projects()
worktime = await client.get_worktime(year=2026, month=1)

# Build a project name lookup
project_names = {p.id: p.name_stripped for p in projects}

# Sum hours by project
for entry in worktime:
    if entry.has_project:
        project_name = project_names.get(entry.project_id, "Unknown")
        print(f"{entry.date}: {entry.duration} on {project_name}")
```

## API v2 (personal tokens)

Timebutler's [API v2](https://app.timebutler.com/api/v2/docs) is JSON-based and acts **as the user** who owns the token.
All v2 operations are supported. Create a personal token (prefix `tb_`) in Timebutler and pass it as `personal_token`:

```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from timebutler_client import TimebutlerClient

client = TimebutlerClient(personal_token="tb_...")

# Book a time entry (start/end must be timezone-aware and on the same day)
berlin = ZoneInfo("Europe/Berlin")
projects = await client.get_time_tracking_projects()
await client.create_time_entry(
    start=datetime(2026, 10, 9, 9, 0, tzinfo=berlin),
    end=datetime(2026, 10, 9, 17, 30, tzinfo=berlin),
    pause=timedelta(minutes=30),
    project_id=projects.default_project_id,
    remarks="Sprint review",
)

# Stamp in / out
await client.start_time_clock()
result = await client.stop_time_clock()
if result is not None and result.outcome == "confirmationRequired":
    result = await client.stop_time_clock(break_regulation="apply")

# Approve absences of your team
for request in await client.get_team_absence_requests():
    if request.status == "pending":
        await client.approve_absence_request(request.id)
```

There is no update endpoint for time entries in v2: to correct an entry, `delete_time_entry()` and create it again.
Accounts without 2FA can also log in with `await TimebutlerClient.from_password(username, password)`;
the access token is then refreshed automatically. v2 models live in `timebutler_client.models.v2`.

Both credentials can be combined: `TimebutlerClient(api_key=..., personal_token=...)`.
Calling a method without the credential it needs raises `TimebutlerMissingCredentialsError`.

### v1 vs v2: what works where

| Use case | v1 (`api_key`) | v2 (`personal_token`) |
|---|---|---|
| Absences of all employees for a year | `get_absences(year)` | team requests only, no year filter |
| Users / employees | `get_users()` | `get_employees()` |
| Projects / services incl. inactive, budget | `get_projects()`, `get_services()` | active only: `get_time_tracking_projects()`, `get_time_tracking_categories()` |
| Worktime of all users | `get_worktime()` | own entries only: `get_my_time_entries()` |
| Workday schedules | `get_workdays()` | – |
| Create / delete time entries, time clock | – | ✅ |
| Create / update / approve absence requests | – | ✅ |
| Substitute, cancellation and time entry approvals | – | ✅ |

### Regenerating v2 models

The v2 models are generated from the pinned spec in `spec/timebutler-v2-openapi.json`:

```bash
curl -sL https://app.timebutler.com/api/v2/openapi.json -o spec/timebutler-v2-openapi.json
uv run --group codegen python scripts/generate_v2_models.py
```

### Integration tests

Read-only smoke tests against the real API (skipped by default):

```bash
TIMEBUTLER_PERSONAL_TOKEN=tb_... uv run --group tests pytest -m integration
```

## Development

This project is based on the [Hochfrequenz Python Template Repository](https://github.com/Hochfrequenz/python_template_repository).
Refer to that repository for detailed setup instructions including [uv](https://docs.astral.sh/uv/) configuration and IDE setup.

### Quick Start

```bash
# Create dev environment
uv sync --group dev

# Run tests
uv run --group tests pytest

# Run linting
uv run --group linting ruff check src/timebutler_client unittests

# Run formatting checks
uv run --group linting ruff format --check .

# Run type checking
uv run --group type_check mypy --strict src/timebutler_client
uv run --group type_check mypy --strict unittests
```

## License

MIT
