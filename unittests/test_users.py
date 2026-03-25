"""Tests for TimebutlerClient.get_users()"""

from datetime import date

import pytest
from aioresponses import aioresponses

from timebutler_client import (
    TimebutlerAuthenticationError,
    TimebutlerClient,
    TimebutlerParseError,
    TimebutlerRateLimitError,
    TimebutlerServerError,
    User,
)

# pylint: disable=line-too-long
SAMPLE_CSV = """\
User ID;Last name;First name;Employee number;E-mail address;Phone;Mobile phone;Cost center;Branch office;Department;User type;Language;User ID list of the user's manager;User account locked;Additional Information;Date of entry (dd/mm/yyyy);Date of separation from company (dd/mm/yyyy);Day of birth (dd/mm/yyyy)
928812;Müller;Anna;00123;anna.mueller@example.com;+49 211 123456;+49 170 654321;CC-01;Düsseldorf;Engineering;Employee;de_DE;100001;false;Senior Dev;01/03/2019;;15/04/1988
322219;Schmidt;Bob;00160;bob.schmidt@example.com;;;;; ;Engineering;Employee;de_DE;100001;false;;;
300224;Fischer;Clara;00042;clara.fischer@example.com;;;;; ;IT;Manager;de_DE;;false;;01/07/2015;31/12/2025;
100001;Weber;Dirk;00001;dirk.weber@example.com;;;;; ;IT;Admin;de_DE;;false;;;"""
# pylint: enable=line-too-long

RESPONSE_HEADERS = {
    "date": "Wed, 25 Mar 2026 10:00:00 GMT",
    "content-type": "text/csv;charset=UTF-8",
    "server": "nginx/1.24.0",
    "set-cookie": "lc=de_DE; Max-Age=46656000; Expires=Thu, 17 Sep 2027 10:00:00 GMT; Path=/; HttpOnly",
    "content-disposition": "attachment;filename=api-result-2026.03.25-10.00.00.csv",
}

EXPECTED_USERS: list[User] = [
    User(
        user_id=928812,
        last_name="Müller",
        first_name="Anna",
        employee_number="00123",
        email="anna.mueller@example.com",
        phone="+49 211 123456",
        mobile_phone="+49 170 654321",
        cost_center="CC-01",
        branch_office="Düsseldorf",
        department="Engineering",
        user_type="Employee",
        language="de_DE",
        manager_user_ids=[100001],
        account_locked=False,
        additional_information="Senior Dev",
        date_of_entry=date(2019, 3, 1),
        date_of_separation=None,
        date_of_birth=date(1988, 4, 15),
    ),
    User(
        user_id=322219,
        last_name="Schmidt",
        first_name="Bob",
        employee_number="00160",
        email="bob.schmidt@example.com",
        user_type="Employee",
        language="de_DE",
        manager_user_ids=[100001],
    ),
    User(
        user_id=300224,
        last_name="Fischer",
        first_name="Clara",
        employee_number="00042",
        email="clara.fischer@example.com",
        user_type="Manager",
        language="de_DE",
        date_of_entry=date(2015, 7, 1),
        date_of_separation=date(2025, 12, 31),
    ),
    User(
        user_id=100001,
        last_name="Weber",
        first_name="Dirk",
        employee_number="00001",
        email="dirk.weber@example.com",
        user_type="Admin",
        language="de_DE",
    ),
]


class TestGetUsers:
    """Tests for TimebutlerClient.get_users()"""

    async def test_get_users_parses_csv_response(self) -> None:
        """Verify CSV response is parsed into User models."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            actual = await client.get_users()

        assert actual == EXPECTED_USERS

    async def test_get_users_sends_auth(self) -> None:
        """Verify auth token is sent as POST data."""
        client = TimebutlerClient(api_key="my-secret-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_users()

            calls = list(mocked.requests.values())[0]
            assert len(calls) == 1
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["auth"] == "my-secret-key"

    async def test_get_users_sends_no_extra_params(self) -> None:
        """Verify no extra parameters are sent (API accepts none)."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_users()

            calls = list(mocked.requests.values())[0]
            request_data = calls[0].kwargs.get("data", {})
            assert set(request_data.keys()) == {"auth"}

    async def test_get_users_raises_on_auth_error(self) -> None:
        """Verify TimebutlerAuthenticationError is raised on 401."""
        client = TimebutlerClient(api_key="bad-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=401,
            )

            with pytest.raises(TimebutlerAuthenticationError):
                await client.get_users()

    async def test_get_users_raises_on_rate_limit(self) -> None:
        """Verify TimebutlerRateLimitError is raised on 429."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=429,
                headers={"Retry-After": "60"},
            )

            with pytest.raises(TimebutlerRateLimitError) as exc_info:
                await client.get_users()

            assert exc_info.value.retry_after == 60

    async def test_get_users_raises_on_server_error(self) -> None:
        """Verify TimebutlerServerError is raised on 5xx."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=500,
                body="Internal Server Error",
            )

            with pytest.raises(TimebutlerServerError) as exc_info:
                await client.get_users()

            assert exc_info.value.status_code == 500

    async def test_get_users_raises_on_malformed_csv(self) -> None:
        """Verify TimebutlerParseError is raised on malformed CSV."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=200,
                headers=RESPONSE_HEADERS,
                body="not;valid;csv\nmissing;required;fields",
            )

            with pytest.raises(TimebutlerParseError):
                await client.get_users()

    async def test_get_users_returns_empty_list_on_empty_csv(self) -> None:
        """Verify empty list is returned when CSV has only headers."""
        client = TimebutlerClient(api_key="test-api-key")
        # pylint: disable=line-too-long
        empty_csv = "User ID;Last name;First name;Employee number;E-mail address;Phone;Mobile phone;Cost center;Branch office;Department;User type;Language;User ID list of the user's manager;User account locked;Additional Information;Date of entry (dd/mm/yyyy);Date of separation from company (dd/mm/yyyy);Day of birth (dd/mm/yyyy)"
        # pylint: enable=line-too-long

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/users",
                status=200,
                headers=RESPONSE_HEADERS,
                body=empty_csv,
            )

            result = await client.get_users()

        assert result == []


class TestUserComputedProperties:
    """Tests for User computed properties."""

    def test_full_name_property(self) -> None:
        """Verify full_name combines first and last name."""
        user = User(user_id=1, last_name="Müller", first_name="Anna", employee_number="00123")
        assert user.full_name == "Anna Müller"

    def test_employee_number_numeric_property(self) -> None:
        """Verify employee_number_numeric removes leading zeros."""
        user = User(user_id=1, last_name="Test", first_name="User", employee_number="00123")
        assert user.employee_number_numeric == 123

    def test_is_active_property(self) -> None:
        """Verify is_active reflects account_locked state."""
        active_user = User(user_id=1, last_name="Test", first_name="User", employee_number="00001", account_locked=False)
        locked_user = User(user_id=2, last_name="Test", first_name="User", employee_number="00002", account_locked=True)
        assert active_user.is_active is True
        assert locked_user.is_active is False

    def test_manager_user_ids_parsed_from_comma_separated_string(self) -> None:
        """Verify manager_user_ids parses comma-separated strings correctly."""
        user = User(
            user_id=1,
            last_name="Test",
            first_name="User",
            employee_number="00001",
            manager_user_ids="100001,100002",  # type: ignore[arg-type]
        )
        assert user.manager_user_ids == [100001, 100002]

    def test_optional_dates_accept_none_and_empty_string(self) -> None:
        """Verify optional date fields accept None and empty strings."""
        user = User(
            user_id=1,
            last_name="Test",
            first_name="User",
            employee_number="00001",
            date_of_entry=None,
            date_of_separation="",  # type: ignore[arg-type]
        )
        assert user.date_of_entry is None
        assert user.date_of_separation is None
