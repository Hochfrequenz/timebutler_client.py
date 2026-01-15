"""Tests for TimebutlerClient.get_absences()"""

from datetime import date
from decimal import Decimal

from aioresponses import aioresponses

from timebutler_client import Absence, TimebutlerClient


# pylint: disable=line-too-long
SAMPLE_CSV = """\
ID;From;To;Half a day;Morning;User ID;Employee number;Type;Extra vacation day;State;Substitute state;Workdays;Hours;Medical certificate (sick leave only);Comments;User ID of the substitute
20001234;15/05/2026;15/05/2026;false;false;928812;00123;Vacation;false;Approved;No approval required;1.0;0.0; ; ;300224
29502809;03/08/2026;07/08/2026;false;false;928812;00123;Vacation;false;Approved;No approval required;5.0;0.0; ; ;300224
29192299;22/05/2026;22/05/2026;false;false;322219;00160;Vacation;false;Approved;No approval required;1.0;0.0; ; ;0
21892839;30/01/2026;30/01/2026;false;false;322219;00160;Vacation;false;Approved;No approval required;1.0;0.0; ; ;0
23333333;29/01/2026;29/01/2026;false;false;322219;00160;Vacation;false;Approved;No approval required;1.0;0.0; ; ;0
24444444;16/03/2026;20/03/2026;false;false;322219;00160;Vacation;false;Approved;No approval required;5.0;0.0; ; ;0
25555555;14/05/2026;14/05/2026;false;false;322219;00160;Vacation;false;Approved;No approval required;1.0;0.0; ;Sonderurlaub Foo bar blub;0
26666666;26/06/2026;17/07/2026;false;false;322219;00160;Vacation;false;Approved;No approval required;16.0;0.0; ;Hier steht ein langer kommentar des Users. ;0
27777777;02/11/2026;03/11/2026;false;false;322219;00160;Vacation;false;Approved;No approval required;2.0;0.0; ; ;0
28888888;01/01/2026;06/01/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;2.0;0.0; ;Weihnachtsurlaub;0
29999999;28/03/2026;31/03/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;2.0;0.0; ;Ostern I;0
21212121;01/04/2026;08/04/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;4.0;0.0; ;Ostern II;0
22345789;12/02/2026;12/02/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;1.0;0.0; ;Karneval;0
29898989;17/02/2026;17/02/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;1.0;0.0; ;Karneval;0
29000001;19/02/2026;19/02/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;1.0;0.0; ; ;0
29000002;26/02/2026;26/02/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;1.0;0.0; ; ;0
29298298;10/03/2026;10/03/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;1.0;0.0; ; ;0
25435431;19/03/2026;19/03/2026;false;false;300224;00042;Vacation;false;Approved;No approval required;1.0;0.0; ; ;0
28822331;19/01/2026;30/01/2026;false;false;309876;00057;Vacation;false;Approved;No approval required;10.0;0.0; ;Skiurlaub in Österreich;0"""
# pylint: enable=line-too-long

RESPONSE_HEADERS = {
    "date": "Thu, 15 Jan 2026 18:30:09 GMT",
    "content-type": "text/csv;charset=UTF-8",
    "server": "nginx/1.24.0",
    "set-cookie": "lc=de_DE; Max-Age=46656000; Expires=Fri, 09 Jul 2027 18:30:09 GMT; Path=/; HttpOnly",
    "content-disposition": "attachment;filename=api-result-2026.01.15-19.30.09.csv",
}


EXPECTED_ABSENCES: list[Absence] = [
    Absence(
        id=20001234,
        from_date=date(2026, 5, 15),
        to_date=date(2026, 5, 15),
        employee_number="00123",
        user_id=928812,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
        substitute_user_id=300224,
    ),
    Absence(
        id=29502809,
        from_date=date(2026, 8, 3),
        to_date=date(2026, 8, 7),
        employee_number="00123",
        user_id=928812,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("5.0"),
        hours=Decimal("0.0"),
        substitute_user_id=300224,
    ),
    Absence(
        id=29192299,
        from_date=date(2026, 5, 22),
        to_date=date(2026, 5, 22),
        employee_number="00160",
        user_id=322219,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=21892839,
        from_date=date(2026, 1, 30),
        to_date=date(2026, 1, 30),
        employee_number="00160",
        user_id=322219,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=23333333,
        from_date=date(2026, 1, 29),
        to_date=date(2026, 1, 29),
        employee_number="00160",
        user_id=322219,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=24444444,
        from_date=date(2026, 3, 16),
        to_date=date(2026, 3, 20),
        employee_number="00160",
        user_id=322219,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("5.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=25555555,
        from_date=date(2026, 5, 14),
        to_date=date(2026, 5, 14),
        employee_number="00160",
        user_id=322219,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
        comments="Sonderurlaub Foo bar blub",
    ),
    Absence(
        id=26666666,
        from_date=date(2026, 6, 26),
        to_date=date(2026, 7, 17),
        employee_number="00160",
        user_id=322219,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("16.0"),
        hours=Decimal("0.0"),
        comments="Hier steht ein langer kommentar des Users.",
    ),
    Absence(
        id=27777777,
        from_date=date(2026, 11, 2),
        to_date=date(2026, 11, 3),
        employee_number="00160",
        user_id=322219,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("2.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=28888888,
        from_date=date(2026, 1, 1),
        to_date=date(2026, 1, 6),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("2.0"),
        hours=Decimal("0.0"),
        comments="Weihnachtsurlaub",
    ),
    Absence(
        id=29999999,
        from_date=date(2026, 3, 28),
        to_date=date(2026, 3, 31),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("2.0"),
        hours=Decimal("0.0"),
        comments="Ostern I",
    ),
    Absence(
        id=21212121,
        from_date=date(2026, 4, 1),
        to_date=date(2026, 4, 8),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("4.0"),
        hours=Decimal("0.0"),
        comments="Ostern II",
    ),
    Absence(
        id=22345789,
        from_date=date(2026, 2, 12),
        to_date=date(2026, 2, 12),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
        comments="Karneval",
    ),
    Absence(
        id=29898989,
        from_date=date(2026, 2, 17),
        to_date=date(2026, 2, 17),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
        comments="Karneval",
    ),
    Absence(
        id=29000001,
        from_date=date(2026, 2, 19),
        to_date=date(2026, 2, 19),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=29000002,
        from_date=date(2026, 2, 26),
        to_date=date(2026, 2, 26),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=29298298,
        from_date=date(2026, 3, 10),
        to_date=date(2026, 3, 10),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=25435431,
        from_date=date(2026, 3, 19),
        to_date=date(2026, 3, 19),
        employee_number="00042",
        user_id=300224,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("1.0"),
        hours=Decimal("0.0"),
    ),
    Absence(
        id=28822331,
        from_date=date(2026, 1, 19),
        to_date=date(2026, 1, 30),
        employee_number="00057",
        user_id=309876,
        absence_type="Vacation",
        state="Approved",
        substitute_state="No approval required",
        workdays=Decimal("10.0"),
        hours=Decimal("0.0"),
        comments="Skiurlaub in Österreich",
    ),
]


class TestGetAbsences:
    """Tests for TimebutlerClient.get_absences()"""

    async def test_get_absences_parses_csv_response(self) -> None:
        """Verify CSV response is parsed into Absence models."""
        client = TimebutlerClient(api_key="test-api-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/absences",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            actual = await client.get_absences(year=2026)

        assert actual == EXPECTED_ABSENCES

    async def test_get_absences_sends_auth_and_year(self) -> None:
        """Verify auth token and year are sent as POST data."""
        client = TimebutlerClient(api_key="my-secret-key")

        with aioresponses() as mocked:
            mocked.post(
                "https://app.timebutler.com/api/v1/absences",
                status=200,
                headers=RESPONSE_HEADERS,
                body=SAMPLE_CSV,
            )

            await client.get_absences(year=2026)

            calls = list(mocked.requests.values())[0]
            assert len(calls) == 1
            request_data = calls[0].kwargs.get("data", {})
            assert request_data["auth"] == "my-secret-key"
            assert request_data["year"] == "2026"
