"""Tests for TimebutlerClient.get_projects()"""

from datetime import date

import pytest
from aioresponses import aioresponses

from timebutler_client import (
    Project,
    TimebutlerAuthenticationError,
    TimebutlerClient,
    TimebutlerParseError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
)

# pylint: disable=line-too-long
SAMPLE_CSV = """\
ID of the project;Name;State;Budget in hours;Comments;Creation date
34343;ABC1234 | Kunde ABC - X-Projekt             ;Active;0; ;23/08/2024
92343;DEF5678 | DEF Customer - div. Projekte;Active;0; ;08/07/2025
33221;GHI9012 | Großkunde - Super Projekt;Active;0; ;11/08/2025
11998;QWE9877 | Anderer Konzern - Tagesgeschäft;Active;0; ;03/05/2023
33482;FOOB1234 | Jener Laden - Foo Bar (bla bla bla);Inactive;0; ;22/04/2021"""
# pylint: enable=line-too-long

RESPONSE_HEADERS = {
    "date": "Fri, 16 Jan 2026 07:34:40 GMT",
    "content-type": "text/csv;charset=UTF-8",
    "server": "nginx/1.24.0",
    "set-cookie": "lc=de_DE; Max-Age=46656000; Expires=Sat, 10 Jul 2027 07:34:40 GMT; Path=/; HttpOnly",
    "content-disposition": "attachment;filename=api-result-2026.01.16-8.34.40.csv",
}


EXPECTED_PROJECTS: list[Project] = [
    Project(
        id=34343,
        name="ABC1234 | Kunde ABC - X-Projekt             ",
        state="Active",
        budget_hours=0,
        creation_date=date(2024, 8, 23),
    ),
    Project(
        id=92343,
        name="DEF5678 | DEF Customer - div. Projekte",
        state="Active",
        budget_hours=0,
        creation_date=date(2025, 7, 8),
    ),
    Project(
        id=33221,
        name="GHI9012 | Großkunde - Super Projekt",
        state="Active",
        budget_hours=0,
        creation_date=date(2025, 8, 11),
    ),
    Project(
        id=11998,
        name="QWE9877 | Anderer Konzern - Tagesgeschäft",
        state="Active",
        budget_hours=0,
        creation_date=date(2023, 5, 3),
    ),
    Project(
        id=33482,
        name="FOOB1234 | Jener Laden - Foo Bar (bla bla bla)",
        state="Inactive",
        budget_hours=0,
        creation_date=date(2021, 4, 22),
    ),
]


class TestGetProjects:
    """Tests for TimebutlerClient.get_projects()"""

    async def test_get_projects_parses_csv_response(self) -> None:
        """Verify CSV response is parsed into Project models."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            actual = await client.get_projects()

        assert actual == EXPECTED_PROJECTS

    async def test_get_projects_sends_auth(self) -> None:
        """Verify auth token is sent as POST data."""
        client = TimebutlerClient(api_key="my-secret-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_projects()

            calls = list(mocked.requests.values())[0]
            assert len(calls) == 1
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["auth"] == "my-secret-key"

    async def test_get_projects_raises_on_auth_error(self) -> None:
        """Verify TimebutlerAuthenticationError is raised on 401."""
        client = TimebutlerClient(api_key="bad-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=401,
            )

            with pytest.raises(TimebutlerAuthenticationError):
                await client.get_projects()

    async def test_get_projects_raises_on_rate_limit(self) -> None:
        """Verify TimebutlerRateLimitError is raised on 429."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=429,
                headers={"Retry-After": "60"},
            )

            with pytest.raises(TimebutlerRateLimitError) as exc_info:
                await client.get_projects()

            assert exc_info.value.retry_after == 60

    async def test_get_projects_raises_on_server_error(self) -> None:
        """Verify TimebutlerServerError is raised on 5xx."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=500,
                body="Internal Server Error",
            )

            with pytest.raises(TimebutlerServerError) as exc_info:
                await client.get_projects()

            assert exc_info.value.status_code == 500

    async def test_get_projects_raises_on_malformed_csv(self) -> None:
        """Verify TimebutlerParseError is raised on malformed CSV."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=200,
                headers=RESPONSE_HEADERS,
                body="not;valid;csv\nmissing;required;fields",
            )

            with pytest.raises(TimebutlerParseError):
                await client.get_projects()

    async def test_get_projects_returns_empty_list_on_empty_csv(self) -> None:
        """Verify empty list is returned when CSV has only headers."""
        client = TimebutlerClient(api_key="test-api-key")
        empty_csv = "ID of the project;Name;State;Budget in hours;Comments;Creation date"

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=200,
                headers=RESPONSE_HEADERS,
                body=empty_csv,
            )

            result = await client.get_projects()

        assert result == []

    async def test_project_name_stripped(self) -> None:
        """Verify name_stripped property removes whitespace."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            projects = await client.get_projects()

        # First project has trailing whitespace in name
        assert projects[0].name == "ABC1234 | Kunde ABC - X-Projekt             "
        assert projects[0].name_stripped == "ABC1234 | Kunde ABC - X-Projekt"

    async def test_project_is_active(self) -> None:
        """Verify is_active property returns correct value."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/projects",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            projects = await client.get_projects()

        assert projects[0].is_active is True  # Active
        assert projects[4].is_active is False  # Inactive
