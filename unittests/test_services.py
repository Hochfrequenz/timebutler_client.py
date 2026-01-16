"""Tests for TimebutlerClient.get_services()"""

from datetime import date

import pytest
from aioresponses import aioresponses

from timebutler_client import (
    Service,
    TimebutlerAuthenticationError,
    TimebutlerClient,
    TimebutlerParseError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
)

# Sample CSV from production API (header only - no services configured)
SAMPLE_CSV_EMPTY = "ID of the service;Name;State;Billable;Comments;Creation date"

# Sample CSV with data for testing parsing
SAMPLE_CSV_WITH_DATA = """\
ID of the service;Name;State;Billable;Comments;Creation date
1001;Development;Active;true;Software development work;15/03/2023
1002;Consulting;Active;true; ;22/06/2024
1003;Internal;Active;false;Non-billable internal work;01/01/2022
1004;Training;Inactive;true;Deprecated training service;10/10/2020"""

RESPONSE_HEADERS = {
    "date": "Fri, 16 Jan 2026 07:48:32 GMT",
    "content-type": "text/csv;charset=UTF-8",
    "server": "nginx/1.24.0",
    "set-cookie": "lc=de_DE; Max-Age=46656000; Expires=Sat, 10 Jul 2027 07:48:32 GMT; Path=/; HttpOnly",
    "content-disposition": "attachment;filename=api-result-2026.01.16-8.48.32.csv",
}


EXPECTED_SERVICES: list[Service] = [
    Service(
        id=1001,
        name="Development",
        state="Active",
        billable=True,
        comments="Software development work",
        creation_date=date(2023, 3, 15),
    ),
    Service(
        id=1002,
        name="Consulting",
        state="Active",
        billable=True,
        creation_date=date(2024, 6, 22),
    ),
    Service(
        id=1003,
        name="Internal",
        state="Active",
        billable=False,
        comments="Non-billable internal work",
        creation_date=date(2022, 1, 1),
    ),
    Service(
        id=1004,
        name="Training",
        state="Inactive",
        billable=True,
        comments="Deprecated training service",
        creation_date=date(2020, 10, 10),
    ),
]


class TestGetServices:
    """Tests for TimebutlerClient.get_services()"""

    async def test_get_services_parses_csv_response(self) -> None:
        """Verify CSV response is parsed into Service models."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV_WITH_DATA,
            )

            actual = await client.get_services()

        assert actual == EXPECTED_SERVICES

    async def test_get_services_sends_auth(self) -> None:
        """Verify auth token is sent as POST data."""
        client = TimebutlerClient(api_key="my-secret-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV_EMPTY,
            )

            await client.get_services()

            calls = list(mocked.requests.values())[0]
            assert len(calls) == 1
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["auth"] == "my-secret-key"

    async def test_get_services_raises_on_auth_error(self) -> None:
        """Verify TimebutlerAuthenticationError is raised on 401."""
        client = TimebutlerClient(api_key="bad-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=401,
            )

            with pytest.raises(TimebutlerAuthenticationError):
                await client.get_services()

    async def test_get_services_raises_on_rate_limit(self) -> None:
        """Verify TimebutlerRateLimitError is raised on 429."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=429,
                headers={"Retry-After": "60"},
            )

            with pytest.raises(TimebutlerRateLimitError) as exc_info:
                await client.get_services()

            assert exc_info.value.retry_after == 60

    async def test_get_services_raises_on_server_error(self) -> None:
        """Verify TimebutlerServerError is raised on 5xx."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=500,
                body="Internal Server Error",
            )

            with pytest.raises(TimebutlerServerError) as exc_info:
                await client.get_services()

            assert exc_info.value.status_code == 500

    async def test_get_services_raises_on_malformed_csv(self) -> None:
        """Verify TimebutlerParseError is raised on malformed CSV."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=200,
                headers=RESPONSE_HEADERS,
                body="not;valid;csv\nmissing;required;fields",
            )

            with pytest.raises(TimebutlerParseError):
                await client.get_services()

    async def test_get_services_returns_empty_list_on_empty_csv(self) -> None:
        """Verify empty list is returned when CSV has only headers."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV_EMPTY,
            )

            result = await client.get_services()

        assert result == []

    async def test_service_name_stripped(self) -> None:
        """Verify name_stripped property removes whitespace."""
        service = Service(
            id=1,
            name="  Service Name  ",
            state="Active",
            creation_date=date(2023, 1, 1),
        )
        assert service.name_stripped == "Service Name"

    async def test_service_is_active(self) -> None:
        """Verify is_active property returns correct value."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV_WITH_DATA,
            )

            services = await client.get_services()

        assert services[0].is_active is True  # Active
        assert services[3].is_active is False  # Inactive

    async def test_service_billable_parsing(self) -> None:
        """Verify billable field is correctly parsed."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/services",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV_WITH_DATA,
            )

            services = await client.get_services()

        assert services[0].billable is True  # Development - billable
        assert services[2].billable is False  # Internal - not billable
