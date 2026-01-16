# Timebutler Client - Projects, Services, and Worktime Endpoints

## Overview

Extend the async Python client with three new endpoints to track where users spend their time:
- **Projects** - project definitions
- **Services** - service definitions
- **Worktime** - time entries linking users to projects/services

## API Details

All endpoints use HTTP POST with `auth` parameter in form data. Responses are semicolon-delimited CSV, UTF-8 encoded.

### Projects Endpoint

- **URL:** `https://app.timebutler.com/api/v1/projects`
- **Parameters:** `auth` (required)
- **Response columns:** ID of the project, Name, State, Budget in hours, Comments, Creation date

### Services Endpoint

- **URL:** `https://app.timebutler.com/api/v1/services`
- **Parameters:** `auth` (required)
- **Response columns:** ID of the service, Name, State, Billable, Comments, Creation date

### Worktime Endpoint

- **URL:** `https://app.timebutler.com/api/v1/worktime`
- **Parameters:**
  - `auth` (required)
  - `year` - Calendar year, defaults to current year
  - `month` - Month 1-12, defaults to current month
  - `userid` - Filter by specific user ID (optional)
- **Response columns:** ID of the work time entry, User ID, Employee number, Date (dd/mm/yyyy), Start time (hh:mm), End time (hh:mm), Working time in seconds, Pause in seconds, State, ID of the project, ID of the service, Comments, Auto stopped

## Models

### Project

```python
class Project(BaseModel):
    """
    Represents a project from Timebutler.

    Projects are used to categorize worktime entries. The name field
    is free text set by users and may contain trailing whitespace.
    """

    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Unique project identifier")
    name: str = Field(description="Project name (free text, may contain whitespace)")
    state: str = Field(description="Project state: 'Active' or 'Inactive'")
    budget_hours: int = Field(default=0, description="Budget in hours, 0 if not set")
    comments: str | None = Field(default=None, description="Optional comments")
    creation_date: EuropeanDate = Field(description="Date the project was created")

    # Computed properties
    @computed_field
    @property
    def name_stripped(self) -> str:
        """Project name with leading/trailing whitespace removed."""
        return self.name.strip()

    @computed_field
    @property
    def is_active(self) -> bool:
        """True if project state is Active."""
        return self.state == "Active"
```

### Service

```python
class Service(BaseModel):
    """
    Represents a service from Timebutler.

    Services are used to categorize worktime entries by type of work.
    """

    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Unique service identifier")
    name: str = Field(description="Service name (free text, may contain whitespace)")
    state: str = Field(description="Service state: 'Active' or 'Inactive'")
    billable: bool = Field(default=False, description="Whether the service is billable")
    comments: str | None = Field(default=None, description="Optional comments")
    creation_date: EuropeanDate = Field(description="Date the service was created")

    # Computed properties
    @computed_field
    @property
    def name_stripped(self) -> str:
        """Service name with leading/trailing whitespace removed."""
        return self.name.strip()

    @computed_field
    @property
    def is_active(self) -> bool:
        """True if service state is Active."""
        return self.state == "Active"
```

### WorktimeEntry

```python
class WorktimeEntry(BaseModel):
    """
    Represents a worktime entry from Timebutler.

    Each entry records time spent by an employee, optionally linked
    to a project and/or service. Times are in 24-hour format.
    """

    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Unique worktime entry identifier")
    user_id: int = Field(description="User ID of the employee")
    employee_number: EmployeeNumber = Field(description="Employee number with leading zeros, e.g. '00123'")
    date: EuropeanDate = Field(description="Date of the worktime entry")
    start_time: time = Field(description="Start time in HH:MM format")
    end_time: time = Field(description="End time in HH:MM format")
    working_time_seconds: int = Field(description="Working time in seconds (excludes pause)")
    pause_seconds: int = Field(default=0, description="Pause duration in seconds")
    state: str = Field(description="Entry state: Done, Requested, Accepted, Rejected, or In process")
    project_id: int = Field(default=0, description="Project ID, 0 if no project assigned")
    service_id: int = Field(default=0, description="Service ID, 0 if no service assigned")
    comments: str | None = Field(default=None, description="Optional comments")
    auto_stopped: bool = Field(default=False, description="Whether the entry was auto-stopped")

    # Computed properties
    @computed_field
    @property
    def duration(self) -> timedelta:
        """Working time as timedelta (excludes pause)."""
        return timedelta(seconds=self.working_time_seconds)

    @computed_field
    @property
    def pause(self) -> timedelta:
        """Pause duration as timedelta."""
        return timedelta(seconds=self.pause_seconds)

    @computed_field
    @property
    def has_project(self) -> bool:
        """True if a project is assigned."""
        return self.project_id != 0

    @computed_field
    @property
    def has_service(self) -> bool:
        """True if a service is assigned."""
        return self.service_id != 0

    @computed_field
    @property
    def employee_number_numeric(self) -> int:
        """Employee number without leading zeros."""
        return int(self.employee_number)
```

## Client Methods

```python
async def get_projects(self) -> list[Project]:
    """
    Fetch all projects.

    Returns:
        List of Project objects (both active and inactive)

    Raises:
        TimebutlerAuthenticationError: If API key is invalid
        TimebutlerRateLimitError: If rate limit is exceeded
        TimebutlerServerError: If server returns 5xx error
        TimebutlerParseError: If response cannot be parsed
    """

async def get_services(self) -> list[Service]:
    """
    Fetch all services.

    Returns:
        List of Service objects (both active and inactive)

    Raises:
        TimebutlerAuthenticationError: If API key is invalid
        TimebutlerRateLimitError: If rate limit is exceeded
        TimebutlerServerError: If server returns 5xx error
        TimebutlerParseError: If response cannot be parsed
    """

async def get_worktime(
    self,
    year: int | None = None,
    month: int | None = None,
    user_id: int | None = None,
) -> list[WorktimeEntry]:
    """
    Fetch worktime entries.

    Args:
        year: Calendar year (defaults to current year if omitted)
        month: Month 1-12 (defaults to current month if omitted)
        user_id: Filter by specific user ID (optional)

    Returns:
        List of WorktimeEntry objects

    Raises:
        ValueError: If month is outside 1-12 range
        TimebutlerAuthenticationError: If API key is invalid
        TimebutlerRateLimitError: If rate limit is exceeded
        TimebutlerServerError: If server returns 5xx error
        TimebutlerParseError: If response cannot be parsed
    """
```

## File Structure

```
src/timebutler_client/
    models/
        __init__.py         # Updated: export Project, Service, WorktimeEntry
        absence.py          # Existing
        project.py          # New
        service.py          # New
        worktime.py         # New
    client.py               # Updated: add get_projects, get_services, get_worktime

unittests/
    test_absences.py        # Existing
    test_projects.py        # New
    test_services.py        # New
    test_worktime.py        # New
```

## Testing

Each test file follows the same pattern:
- Exact response headers from production API samples
- Full CSV payloads from provided samples
- Verify auth token is sent correctly as POST data
- Compare full model lists

### Sample Test Data

**Projects CSV:**
```csv
ID of the project;Name;State;Budget in hours;Comments;Creation date
34343;ABC1234 | Kunde ABC - X-Projekt             ;Active;0; ;23/08/2024
92343;DEF5678 | DEF Customer - div. Projekte;Active;0; ;08/07/2025
33221;GHI9012 | Großkunde - Super Projekt;Active;0; ;11/08/2025
11998;QWE9877 | Anderer Konzern - Tagesgeschäft;Active;0; ;03/05/2023
33482;FOOB1234 | Jener Laden - Foo Bar (bla bla bla);Inactive;0; ;22/04/2021
```

**Services CSV:**
```csv
ID of the service;Name;State;Billable;Comments;Creation date
```
(Empty - header only in sample)

**Worktime CSV:**
```csv
ID of the work time entry;User ID;Employee number;Date (dd/mm/yyyy);Start time (hh:mm);End time (hh:mm);Working time in seconds;Pause in seconds;State;ID of the project;ID of the service;Comments;Auto stopped
56789012;998877;00123;02/01/2026;07:00;12:30;19800;0;Done;23456;0; ;false
51234567;998877;00123;05/01/2026;07:00;15:00;27000;1800;Done;23456;0; ;false
89012344;998877;00123;05/01/2026;15:00;15:30;1800;0;Done;20267;0; ;false
23457890;998877;00123;06/01/2026;06:00;14:30;28800;1800;Done;23456;0; ;false
65432102;998877;00123;07/01/2026;10:00;10:30;1800;0;Done;20267;0; ;false
88229912;998877;00123;07/01/2026;07:00;10:00;10800;0;Done;23456;0; ;false
28910229;998877;00123;07/01/2026;10:30;17:15;21600;2700;Done;23456;0; ;false
```

### Response Headers for Mocks

```python
{
    "date": "Fri, 16 Jan 2026 07:34:40 GMT",
    "content-type": "text/csv;charset=UTF-8",
    "server": "nginx/1.24.0",
    "set-cookie": "lc=de_DE; Max-Age=46656000; Expires=Sat, 10 Jul 2027 07:34:40 GMT; Path=/; HttpOnly",
    "content-disposition": "attachment;filename=api-result-2026.01.16-8.34.40.csv",
}
```

## Implementation Notes

- Each endpoint gets its own `_parse_*_csv` method (no shared abstraction)
- Reuse existing `EuropeanDate` and `EmployeeNumber` types from `absence.py`
- Reuse existing exception classes for error handling
- Name fields preserve whitespace; use `name_stripped` property for cleaned version
- IDs of 0 mean "no project/service assigned"
- Time parsing uses `datetime.strptime(value, "%H:%M").time()` for HH:MM format

## Implementation Checklist

- [ ] Create `models/project.py` with Project model
- [ ] Create `models/service.py` with Service model
- [ ] Create `models/worktime.py` with WorktimeEntry model
- [ ] Update `models/__init__.py` to export new models
- [ ] Add `get_projects()` method to client
- [ ] Add `get_services()` method to client
- [ ] Add `get_worktime()` method to client
- [ ] Add `_parse_projects_csv()` method
- [ ] Add `_parse_services_csv()` method
- [ ] Add `_parse_worktime_csv()` method
- [ ] Update `__init__.py` to export new models
- [ ] Create `test_projects.py` with mock tests
- [ ] Create `test_services.py` with mock tests
- [ ] Create `test_worktime.py` with mock tests
- [ ] Run tests and linting
