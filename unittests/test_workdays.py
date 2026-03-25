"""Tests for TimebutlerClient.get_workdays()"""

from datetime import date, timedelta

import pytest
from aioresponses import aioresponses

from timebutler_client import (
    TimebutlerAuthenticationError,
    TimebutlerClient,
    TimebutlerParseError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
    WorkdaySchedule,
)

# pylint: disable=line-too-long
SAMPLE_CSV = """\
User ID;Valid from (dd/mm/yyyy);Monday working time in minutes;Tuesday working time in minutes;Wednesday working time in minutes;Thursday working time in minutes;Friday working time in minutes;Saturday working time in minutes;Sunday working time in minutes;ID of the holiday set
928812;01/01/2020;480;480;480;480;480;0;0;42
928812;01/03/2024;480;480;480;480;240;0;0;42
322219;01/01/2021;480;480;480;480;480;0;0;42
300224;01/06/2019;480;480;480;480;480;0;0;17"""
# pylint: enable=line-too-long

RESPONSE_HEADERS = {
    "date": "Wed, 25 Mar 2026 10:00:00 GMT",
    "content-type": "text/csv;charset=UTF-8",
    "server": "nginx/1.24.0",
    "set-cookie": "lc=de_DE; Max-Age=46656000; Expires=Thu, 17 Sep 2027 10:00:00 GMT; Path=/; HttpOnly",
    "content-disposition": "attachment;filename=api-result-2026.03.25-10.00.00.csv",
}

EXPECTED_SCHEDULES: list[WorkdaySchedule] = [
    WorkdaySchedule(
        user_id=928812,
        valid_from=date(2020, 1, 1),
        monday_minutes=480,
        tuesday_minutes=480,
        wednesday_minutes=480,
        thursday_minutes=480,
        friday_minutes=480,
        saturday_minutes=0,
        sunday_minutes=0,
        holiday_set_id=42,
    ),
    WorkdaySchedule(
        user_id=928812,
        valid_from=date(2024, 3, 1),
        monday_minutes=480,
        tuesday_minutes=480,
        wednesday_minutes=480,
        thursday_minutes=480,
        friday_minutes=240,
        saturday_minutes=0,
        sunday_minutes=0,
        holiday_set_id=42,
    ),
    WorkdaySchedule(
        user_id=322219,
        valid_from=date(2021, 1, 1),
        monday_minutes=480,
        tuesday_minutes=480,
        wednesday_minutes=480,
        thursday_minutes=480,
        friday_minutes=480,
        saturday_minutes=0,
        sunday_minutes=0,
        holiday_set_id=42,
    ),
    WorkdaySchedule(
        user_id=300224,
        valid_from=date(2019, 6, 1),
        monday_minutes=480,
        tuesday_minutes=480,
        wednesday_minutes=480,
        thursday_minutes=480,
        friday_minutes=480,
        saturday_minutes=0,
        sunday_minutes=0,
        holiday_set_id=17,
    ),
]


class TestGetWorkdays:
    """Tests for TimebutlerClient.get_workdays()"""

    async def test_get_workdays_parses_csv_response(self) -> None:
        """Verify CSV response is parsed into WorkdaySchedule models."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            actual = await client.get_workdays()

        assert actual == EXPECTED_SCHEDULES

    async def test_get_workdays_sends_auth(self) -> None:
        """Verify auth token is sent as POST data."""
        client = TimebutlerClient(api_key="my-secret-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_workdays()

            calls = list(mocked.requests.values())[0]
            assert len(calls) == 1
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["auth"] == "my-secret-key"

    async def test_get_workdays_sends_no_extra_params(self) -> None:
        """Verify no extra parameters are sent (API accepts none)."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_workdays()

            calls = list(mocked.requests.values())[0]
            request_data = calls[0].kwargs.get("data", {})
            assert set(request_data.keys()) == {"auth"}

    async def test_get_workdays_raises_on_auth_error(self) -> None:
        """Verify TimebutlerAuthenticationError is raised on 401."""
        client = TimebutlerClient(api_key="bad-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=401,
            )

            with pytest.raises(TimebutlerAuthenticationError):
                await client.get_workdays()

    async def test_get_workdays_raises_on_rate_limit(self) -> None:
        """Verify TimebutlerRateLimitError is raised on 429."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=429,
                headers={"Retry-After": "60"},
            )

            with pytest.raises(TimebutlerRateLimitError) as exc_info:
                await client.get_workdays()

            assert exc_info.value.retry_after == 60

    async def test_get_workdays_raises_on_server_error(self) -> None:
        """Verify TimebutlerServerError is raised on 5xx."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=500,
                body="Internal Server Error",
            )

            with pytest.raises(TimebutlerServerError) as exc_info:
                await client.get_workdays()

            assert exc_info.value.status_code == 500

    async def test_get_workdays_raises_on_malformed_csv(self) -> None:
        """Verify TimebutlerParseError is raised on malformed CSV."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=200,
                headers=RESPONSE_HEADERS,
                body="not;valid;csv\nmissing;required;fields",
            )

            with pytest.raises(TimebutlerParseError):
                await client.get_workdays()

    async def test_get_workdays_returns_empty_list_on_empty_csv(self) -> None:
        """Verify empty list is returned when CSV has only headers."""
        client = TimebutlerClient(api_key="test-api-key")
        # pylint: disable=line-too-long
        empty_csv = "User ID;Valid from (dd/mm/yyyy);Monday working time in minutes;Tuesday working time in minutes;Wednesday working time in minutes;Thursday working time in minutes;Friday working time in minutes;Saturday working time in minutes;Sunday working time in minutes;ID of the holiday set"
        # pylint: enable=line-too-long

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=200,
                headers=RESPONSE_HEADERS,
                body=empty_csv,
            )

            result = await client.get_workdays()

        assert result == []

    async def test_get_workdays_multiple_entries_per_user(self) -> None:
        """Verify multiple schedule entries for the same user are returned."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/workdays",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            result = await client.get_workdays()

        user_928812_entries = [s for s in result if s.user_id == 928812]
        assert len(user_928812_entries) == 2


class TestWorkdayScheduleComputedProperties:
    """Tests for WorkdaySchedule computed properties."""

    def test_weekday_timedelta_properties(self) -> None:
        """Verify weekday timedelta properties convert minutes correctly."""
        schedule = WorkdaySchedule(
            user_id=1,
            valid_from=date(2026, 1, 1),
            monday_minutes=480,
            tuesday_minutes=480,
            wednesday_minutes=480,
            thursday_minutes=480,
            friday_minutes=240,
            saturday_minutes=0,
            sunday_minutes=0,
            holiday_set_id=1,
        )
        assert schedule.monday == timedelta(hours=8)
        assert schedule.tuesday == timedelta(hours=8)
        assert schedule.wednesday == timedelta(hours=8)
        assert schedule.thursday == timedelta(hours=8)
        assert schedule.friday == timedelta(hours=4)
        assert schedule.saturday == timedelta(0)
        assert schedule.sunday == timedelta(0)

    def test_weekly_minutes_property(self) -> None:
        """Verify weekly_minutes sums all days."""
        schedule = WorkdaySchedule(
            user_id=1,
            valid_from=date(2026, 1, 1),
            monday_minutes=480,
            tuesday_minutes=480,
            wednesday_minutes=480,
            thursday_minutes=480,
            friday_minutes=480,
        )
        assert schedule.weekly_minutes == 2400

    def test_weekly_duration_property(self) -> None:
        """Verify weekly_duration returns correct timedelta."""
        schedule = WorkdaySchedule(
            user_id=1,
            valid_from=date(2026, 1, 1),
            monday_minutes=480,
            tuesday_minutes=480,
            wednesday_minutes=480,
            thursday_minutes=480,
            friday_minutes=480,
        )
        assert schedule.weekly_duration == timedelta(hours=40)
