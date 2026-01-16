"""Tests for TimebutlerClient.get_worktime()"""

from datetime import date, time, timedelta

import pytest
from aioresponses import aioresponses

from timebutler_client import (
    TimebutlerAuthenticationError,
    TimebutlerClient,
    TimebutlerParseError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
    WorktimeEntry,
)

# pylint: disable=line-too-long
SAMPLE_CSV = """\
ID of the work time entry;User ID;Employee number;Date (dd/mm/yyyy);Start time (hh:mm);End time (hh:mm);Working time in seconds;Pause in seconds;State;ID of the project;ID of the service;Comments;Auto stopped
56789012;998877;00123;02/01/2026;07:00;12:30;19800;0;Done;23456;0; ;false
51234567;998877;00123;05/01/2026;07:00;15:00;27000;1800;Done;23456;0; ;false
89012344;998877;00123;05/01/2026;15:00;15:30;1800;0;Done;20267;0; ;false
23457890;998877;00123;06/01/2026;06:00;14:30;28800;1800;Done;23456;0; ;false
65432102;998877;00123;07/01/2026;10:00;10:30;1800;0;Done;20267;0; ;false
88229912;998877;00123;07/01/2026;07:00;10:00;10800;0;Done;23456;0; ;false
28910229;998877;00123;07/01/2026;10:30;17:15;21600;2700;Done;23456;0; ;false"""
# pylint: enable=line-too-long

RESPONSE_HEADERS = {
    "date": "Fri, 16 Jan 2026 07:55:20 GMT",
    "content-type": "text/csv;charset=UTF-8",
    "server": "nginx/1.24.0",
    "set-cookie": "lc=de_DE; Max-Age=46656000; Expires=Sat, 10 Jul 2027 07:55:20 GMT; Path=/; HttpOnly",
    "content-disposition": "attachment;filename=api-result-2026.01.16-8.55.20.csv",
}


EXPECTED_ENTRIES: list[WorktimeEntry] = [
    WorktimeEntry(
        id=56789012,
        user_id=998877,
        employee_number="00123",
        date=date(2026, 1, 2),
        start_time=time(7, 0),
        end_time=time(12, 30),
        working_time_seconds=19800,
        pause_seconds=0,
        state="Done",
        project_id=23456,
        service_id=0,
    ),
    WorktimeEntry(
        id=51234567,
        user_id=998877,
        employee_number="00123",
        date=date(2026, 1, 5),
        start_time=time(7, 0),
        end_time=time(15, 0),
        working_time_seconds=27000,
        pause_seconds=1800,
        state="Done",
        project_id=23456,
        service_id=0,
    ),
    WorktimeEntry(
        id=89012344,
        user_id=998877,
        employee_number="00123",
        date=date(2026, 1, 5),
        start_time=time(15, 0),
        end_time=time(15, 30),
        working_time_seconds=1800,
        pause_seconds=0,
        state="Done",
        project_id=20267,
        service_id=0,
    ),
    WorktimeEntry(
        id=23457890,
        user_id=998877,
        employee_number="00123",
        date=date(2026, 1, 6),
        start_time=time(6, 0),
        end_time=time(14, 30),
        working_time_seconds=28800,
        pause_seconds=1800,
        state="Done",
        project_id=23456,
        service_id=0,
    ),
    WorktimeEntry(
        id=65432102,
        user_id=998877,
        employee_number="00123",
        date=date(2026, 1, 7),
        start_time=time(10, 0),
        end_time=time(10, 30),
        working_time_seconds=1800,
        pause_seconds=0,
        state="Done",
        project_id=20267,
        service_id=0,
    ),
    WorktimeEntry(
        id=88229912,
        user_id=998877,
        employee_number="00123",
        date=date(2026, 1, 7),
        start_time=time(7, 0),
        end_time=time(10, 0),
        working_time_seconds=10800,
        pause_seconds=0,
        state="Done",
        project_id=23456,
        service_id=0,
    ),
    WorktimeEntry(
        id=28910229,
        user_id=998877,
        employee_number="00123",
        date=date(2026, 1, 7),
        start_time=time(10, 30),
        end_time=time(17, 15),
        working_time_seconds=21600,
        pause_seconds=2700,
        state="Done",
        project_id=23456,
        service_id=0,
    ),
]


class TestGetWorktime:
    """Tests for TimebutlerClient.get_worktime()"""

    async def test_get_worktime_parses_csv_response(self) -> None:
        """Verify CSV response is parsed into WorktimeEntry models."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            actual = await client.get_worktime()

        assert actual == EXPECTED_ENTRIES

    async def test_get_worktime_sends_auth(self) -> None:
        """Verify auth token is sent as POST data."""
        client = TimebutlerClient(api_key="my-secret-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_worktime()

            calls = list(mocked.requests.values())[0]
            assert len(calls) == 1
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["auth"] == "my-secret-key"

    async def test_get_worktime_sends_year_and_month(self) -> None:
        """Verify year and month are sent as POST data when provided."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_worktime(year=2026, month=1)

            calls = list(mocked.requests.values())[0]
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["year"] == "2026"
            assert request_data["month"] == "1"

    async def test_get_worktime_sends_user_id_filter(self) -> None:
        """Verify user_id filter is sent as POST data when provided."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_worktime(user_id=998877)

            calls = list(mocked.requests.values())[0]
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["userid"] == "998877"

    async def test_get_worktime_omits_optional_params_when_none(self) -> None:
        """Verify optional params are not sent when None."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_worktime()

            calls = list(mocked.requests.values())[0]
            request_data = calls[0].kwargs.get("data", {})
            assert "year" not in request_data
            assert "month" not in request_data
            assert "userid" not in request_data

    async def test_get_worktime_raises_on_invalid_month(self) -> None:
        """Verify ValueError is raised for invalid month."""
        client = TimebutlerClient(api_key="test-api-key")

        with pytest.raises(ValueError, match="Month must be between 1 and 12"):
            await client.get_worktime(month=0)

        with pytest.raises(ValueError, match="Month must be between 1 and 12"):
            await client.get_worktime(month=13)

    async def test_get_worktime_raises_on_auth_error(self) -> None:
        """Verify TimebutlerAuthenticationError is raised on 401."""
        client = TimebutlerClient(api_key="bad-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=401,
            )

            with pytest.raises(TimebutlerAuthenticationError):
                await client.get_worktime()

    async def test_get_worktime_raises_on_rate_limit(self) -> None:
        """Verify TimebutlerRateLimitError is raised on 429."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=429,
                headers={"Retry-After": "60"},
            )

            with pytest.raises(TimebutlerRateLimitError) as exc_info:
                await client.get_worktime()

            assert exc_info.value.retry_after == 60

    async def test_get_worktime_raises_on_server_error(self) -> None:
        """Verify TimebutlerServerError is raised on 5xx."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=500,
                body="Internal Server Error",
            )

            with pytest.raises(TimebutlerServerError) as exc_info:
                await client.get_worktime()

            assert exc_info.value.status_code == 500

    async def test_get_worktime_raises_on_malformed_csv(self) -> None:
        """Verify TimebutlerParseError is raised on malformed CSV."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=200,
                headers=RESPONSE_HEADERS,
                body="not;valid;csv\nmissing;required;fields",
            )

            with pytest.raises(TimebutlerParseError):
                await client.get_worktime()

    async def test_get_worktime_returns_empty_list_on_empty_csv(self) -> None:
        """Verify empty list is returned when CSV has only headers."""
        client = TimebutlerClient(api_key="test-api-key")
        # pylint: disable=line-too-long
        empty_csv = "ID of the work time entry;User ID;Employee number;Date (dd/mm/yyyy);Start time (hh:mm);End time (hh:mm);Working time in seconds;Pause in seconds;State;ID of the project;ID of the service;Comments;Auto stopped"
        # pylint: enable=line-too-long

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/worktime",
                status=200,
                headers=RESPONSE_HEADERS,
                body=empty_csv,
            )

            result = await client.get_worktime()

        assert result == []


class TestWorktimeEntryComputedProperties:
    """Tests for WorktimeEntry computed properties."""

    def test_duration_property(self) -> None:
        """Verify duration property returns correct timedelta."""
        entry = WorktimeEntry(
            id=1,
            user_id=1,
            employee_number="00001",
            date=date(2026, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_time_seconds=28800,  # 8 hours
            state="Done",
        )
        assert entry.duration == timedelta(hours=8)

    def test_pause_property(self) -> None:
        """Verify pause property returns correct timedelta."""
        entry = WorktimeEntry(
            id=1,
            user_id=1,
            employee_number="00001",
            date=date(2026, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_time_seconds=27000,
            pause_seconds=1800,  # 30 minutes
            state="Done",
        )
        assert entry.pause == timedelta(minutes=30)

    def test_has_project_property(self) -> None:
        """Verify has_project property returns correct value."""
        entry_with_project = WorktimeEntry(
            id=1,
            user_id=1,
            employee_number="00001",
            date=date(2026, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_time_seconds=28800,
            state="Done",
            project_id=123,
        )
        entry_without_project = WorktimeEntry(
            id=2,
            user_id=1,
            employee_number="00001",
            date=date(2026, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_time_seconds=28800,
            state="Done",
            project_id=0,
        )
        assert entry_with_project.has_project is True
        assert entry_without_project.has_project is False

    def test_has_service_property(self) -> None:
        """Verify has_service property returns correct value."""
        entry_with_service = WorktimeEntry(
            id=1,
            user_id=1,
            employee_number="00001",
            date=date(2026, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_time_seconds=28800,
            state="Done",
            service_id=456,
        )
        entry_without_service = WorktimeEntry(
            id=2,
            user_id=1,
            employee_number="00001",
            date=date(2026, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_time_seconds=28800,
            state="Done",
            service_id=0,
        )
        assert entry_with_service.has_service is True
        assert entry_without_service.has_service is False

    def test_employee_number_numeric_property(self) -> None:
        """Verify employee_number_numeric removes leading zeros."""
        entry = WorktimeEntry(
            id=1,
            user_id=1,
            employee_number="00123",
            date=date(2026, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            working_time_seconds=28800,
            state="Done",
        )
        assert entry.employee_number_numeric == 123
