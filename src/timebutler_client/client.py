"""Async client for the Timebutler API."""

import csv
from decimal import Decimal
from io import StringIO

import aiohttp
from pydantic import BaseModel, PrivateAttr

from timebutler_client.models import Absence


class TimebutlerClient(BaseModel):
    """
    Async client for the Timebutler API.

    Example:
        client = TimebutlerClient(api_key="your-api-key")
        absences = await client.get_absences(year=2026)
    """

    base_url: str = "https://app.timebutler.com/api/v1"
    _api_key: str = PrivateAttr()

    def __init__(self, api_key: str, base_url: str = "https://app.timebutler.com/api/v1") -> None:
        super().__init__(base_url=base_url)
        self._api_key = api_key

    async def get_absences(self, year: int) -> list[Absence]:
        """
        Fetch absences for a given year.

        Args:
            year: The year to fetch absences for (e.g., 2026)

        Returns:
            List of Absence objects

        Note:
            Despite being named 'get_', this calls a POST endpoint
            (Timebutler API only accepts POST requests).
        """
        # Session is created per-call for simplicity.
        # For high-throughput scenarios, consider passing a shared session
        # or refactoring to use a context manager pattern.
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/absences",
                data={"auth": self._api_key, "year": str(year)},
            ) as response:
                response.raise_for_status()
                csv_text = await response.text()
                return self._parse_absences_csv(csv_text)

    def _parse_absences_csv(self, csv_text: str) -> list[Absence]:
        """Parse semicolon-delimited CSV into Absence models."""
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
                substitute_user_id=int(row["User ID of the substitute"]) if row.get("User ID of the substitute") else 0,
            )
            absences.append(absence)

        return absences
