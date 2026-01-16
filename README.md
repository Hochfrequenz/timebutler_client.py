# timebutler_client

Async Python client for the [Timebutler](https://timebutler.com) API ([official docs](https://app.timebutler.com/do?ha=api&ac=10)).

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

```python
from timebutler_client import TimebutlerClient

# Create client with your API key
client = TimebutlerClient(api_key="your-api-key")

# Fetch absences for a specific year
absences = await client.get_absences(year=2026)

for absence in absences:
    print(f"{absence.employee_number}: {absence.from_date} - {absence.to_date} ({absence.absence_type})")
```

## Features

> [!NOTE]
> We only implemented a subset of the Timebutler API endpoints, because the API is not very convenient to develop against (no OpenAPI, no sandbox or test system, only admin API keys).

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
| `get_worktime(year?, month?, user_id?)` | Fetch worktime entries with optional filters |

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

## Development

This project is based on the [Hochfrequenz Python Template Repository](https://github.com/Hochfrequenz/python_template_repository).
Refer to that repository for detailed setup instructions including tox configuration and IDE setup.

### Quick Start

```bash
# Create dev environment
tox -e dev

# Run tests
tox -e tests

# Run linting
tox -e linting

# Run type checking
tox -e type_check
```

## License

MIT
