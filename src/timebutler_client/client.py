"""Async client for the Timebutler API."""

import csv
from decimal import Decimal
from io import StringIO

import aiohttp
from pydantic import BaseModel, PrivateAttr

from timebutler_client.exceptions import (
    TimebutlerAuthenticationError,
    TimebutlerParseError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
)
from timebutler_client.models import Absence, Project, Service, WorktimeEntry


class TimebutlerClient(BaseModel):
    """
    Async client for the Timebutler API.

    Example:
        client = TimebutlerClient(api_key="your-api-key")
        absences = await client.get_absences(year=2026)
    """

    base_url: str = "https://app.timebutler.com/api/v1"
    timeout: float = 30.0
    _api_key: str = PrivateAttr()

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.timebutler.com/api/v1",
        timeout: float = 30.0,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout)
        self._api_key = api_key

    def __repr__(self) -> str:
        return f"TimebutlerClient(base_url={self.base_url!r}, api_key='****')"

    async def get_absences(self, year: int) -> list[Absence]:
        """
        Fetch absences for a given year.

        Args:
            year: The year to fetch absences for (e.g., 2026)

        Returns:
            List of Absence objects

        Raises:
            ValueError: If year is outside valid range (1900-2100)
            TimebutlerAuthenticationError: If API key is invalid
            TimebutlerRateLimitError: If rate limit is exceeded
            TimebutlerServerError: If server returns 5xx error
            TimebutlerParseError: If response cannot be parsed

        Note:
            Despite being named 'get_', this calls a POST endpoint
            (Timebutler API only accepts POST requests).
        """
        if not 1900 <= year <= 2100:
            raise ValueError(f"Year must be between 1900 and 2100, got {year}")

        # Session is created per-call for simplicity.
        # For high-throughput scenarios, consider passing a shared session
        # or refactoring to use a context manager pattern.
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.post(
                f"{self.base_url}/absences",
                data={"auth": self._api_key, "year": str(year)},
            ) as response:
                await self._check_response(response)
                csv_text = await response.text()
                return self._parse_absences_csv(csv_text)

    async def _check_response(self, response: aiohttp.ClientResponse) -> None:
        """Check response status and raise appropriate exceptions."""
        if response.status in (401, 403):
            raise TimebutlerAuthenticationError("Invalid API key")
        if response.status == 429:
            retry_after = response.headers.get("Retry-After")
            raise TimebutlerRateLimitError(int(retry_after) if retry_after else None)
        if response.status >= 500:
            text = await response.text()
            raise TimebutlerServerError(response.status, text[:200])
        response.raise_for_status()

    def _parse_absences_csv(self, csv_text: str) -> list[Absence]:
        """Parse semicolon-delimited CSV into Absence models."""
        try:
            reader = csv.DictReader(StringIO(csv_text), delimiter=";")
            absences: list[Absence] = []

            for row in reader:
                absence = Absence(
                    id=int(row["ID"]),
                    from_date=row["From"],  # type: ignore[arg-type]  # BeforeValidator handles str->date
                    to_date=row["To"],  # type: ignore[arg-type]  # BeforeValidator handles str->date
                    employee_number=row["Employee number"],
                    user_id=int(row["User ID"]) if row.get("User ID") else 0,
                    half_day=row.get("Half a day", "").lower() == "true",
                    morning=row.get("Morning", "").lower() == "true",
                    absence_type=row.get("Type", ""),
                    extra_vacation=row.get("Extra vacation day", "").lower() == "true",
                    state=row.get("State", ""),
                    substitute_state=row.get("Substitute state", ""),
                    workdays=Decimal(row["Workdays"]) if row.get("Workdays") else Decimal("0"),
                    hours=Decimal(row["Hours"]) if row.get("Hours") else Decimal("0"),
                    medical_certificate=row.get("Medical certificate (sick leave only)", "").strip() or None,
                    comments=row.get("Comments", "").strip() or None,
                    substitute_user_id=(
                        int(row["User ID of the substitute"]) if row.get("User ID of the substitute") else 0
                    ),
                )
                absences.append(absence)

            return absences
        except (KeyError, ValueError) as e:
            raise TimebutlerParseError(f"Failed to parse API response: {e}") from e

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

        Note:
            Despite being named 'get_', this calls a POST endpoint
            (Timebutler API only accepts POST requests).
        """
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.post(
                f"{self.base_url}/projects",
                data={"auth": self._api_key},
            ) as response:
                await self._check_response(response)
                csv_text = await response.text()
                return self._parse_projects_csv(csv_text)

    def _parse_projects_csv(self, csv_text: str) -> list[Project]:
        """Parse semicolon-delimited CSV into Project models."""
        try:
            reader = csv.DictReader(StringIO(csv_text), delimiter=";")
            projects: list[Project] = []

            for row in reader:
                project = Project(
                    id=int(row["ID of the project"]),
                    name=row["Name"],
                    state=row["State"],
                    budget_hours=int(row["Budget in hours"]) if row.get("Budget in hours") else 0,
                    comments=row.get("Comments", "").strip() or None,
                    creation_date=row["Creation date"],  # type: ignore[arg-type]  # BeforeValidator handles str->date
                )
                projects.append(project)

            return projects
        except (KeyError, ValueError) as e:
            raise TimebutlerParseError(f"Failed to parse API response: {e}") from e

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

        Note:
            Despite being named 'get_', this calls a POST endpoint
            (Timebutler API only accepts POST requests).
        """
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.post(
                f"{self.base_url}/services",
                data={"auth": self._api_key},
            ) as response:
                await self._check_response(response)
                csv_text = await response.text()
                return self._parse_services_csv(csv_text)

    def _parse_services_csv(self, csv_text: str) -> list[Service]:
        """Parse semicolon-delimited CSV into Service models."""
        try:
            reader = csv.DictReader(StringIO(csv_text), delimiter=";")
            services: list[Service] = []

            for row in reader:
                service = Service(
                    id=int(row["ID of the service"]),
                    name=row["Name"],
                    state=row["State"],
                    billable=row.get("Billable", "").lower() == "true",
                    comments=row.get("Comments", "").strip() or None,
                    creation_date=row["Creation date"],  # type: ignore[arg-type]  # BeforeValidator handles str->date
                )
                services.append(service)

            return services
        except (KeyError, ValueError) as e:
            raise TimebutlerParseError(f"Failed to parse API response: {e}") from e

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

        Note:
            Despite being named 'get_', this calls a POST endpoint
            (Timebutler API only accepts POST requests).
        """
        if month is not None and not 1 <= month <= 12:
            raise ValueError(f"Month must be between 1 and 12, got {month}")

        data: dict[str, str] = {"auth": self._api_key}
        if year is not None:
            data["year"] = str(year)
        if month is not None:
            data["month"] = str(month)
        if user_id is not None:
            data["userid"] = str(user_id)

        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.post(
                f"{self.base_url}/worktime",
                data=data,
            ) as response:
                await self._check_response(response)
                csv_text = await response.text()
                return self._parse_worktime_csv(csv_text)

    def _parse_worktime_csv(self, csv_text: str) -> list[WorktimeEntry]:
        """Parse semicolon-delimited CSV into WorktimeEntry models."""
        try:
            reader = csv.DictReader(StringIO(csv_text), delimiter=";")
            entries: list[WorktimeEntry] = []

            for row in reader:
                entry = WorktimeEntry(
                    id=int(row["ID of the work time entry"]),
                    user_id=int(row["User ID"]),
                    employee_number=row["Employee number"],
                    date=row["Date (dd/mm/yyyy)"],  # type: ignore[arg-type]  # BeforeValidator handles str->date
                    start_time=row["Start time (hh:mm)"],  # type: ignore[arg-type]  # BeforeValidator handles str->time
                    end_time=row["End time (hh:mm)"],  # type: ignore[arg-type]  # BeforeValidator handles str->time
                    working_time_seconds=int(row["Working time in seconds"]),
                    pause_seconds=int(row["Pause in seconds"]) if row.get("Pause in seconds") else 0,
                    state=row["State"],
                    project_id=int(row["ID of the project"]) if row.get("ID of the project") else 0,
                    service_id=int(row["ID of the service"]) if row.get("ID of the service") else 0,
                    comments=row.get("Comments", "").strip() or None,
                    auto_stopped=row.get("Auto stopped", "").lower() == "true",
                )
                entries.append(entry)

            return entries
        except (KeyError, ValueError) as e:
            raise TimebutlerParseError(f"Failed to parse API response: {e}") from e
