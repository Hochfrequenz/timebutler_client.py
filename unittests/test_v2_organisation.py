"""Tests for v2 organisation endpoints."""

import pytest
from aioresponses import aioresponses

from timebutler_client import TimebutlerClient, TimebutlerMissingCredentialsError, TimebutlerParseError
from timebutler_client.models.v2 import CategoriesResponse, EmployeeDto, ProjectsResponse
from unittests.v2_helpers import V2, make_client, only_request


class TestOrganisation:
    """employees, projects, categories, profile"""

    async def test_get_employees(self) -> None:
        payload = [{"id": "42", "employeeNumber": "0815", "firstName": "Maria", "lastName": "Müller", "active": True}]
        with aioresponses() as mocked:
            mocked.get(f"{V2}/employees", status=200, payload=payload)
            actual = await make_client().get_employees()
            call = only_request(mocked)
        assert actual == [EmployeeDto.model_validate(payload[0])]
        assert actual[0].employee_number == "0815"
        assert call.kwargs.get("json") is None

    async def test_get_time_tracking_projects(self) -> None:
        payload = {
            "projects": [{"id": "5", "name": "Kunde A", "isFavorite": True}],
            "defaultProjectId": "5",
            "isProjectMandatory": True,
        }
        with aioresponses() as mocked:
            mocked.get(f"{V2}/projects", status=200, payload=payload)
            actual = await make_client().get_time_tracking_projects()
        assert actual == ProjectsResponse.model_validate(payload)
        assert actual.default_project_id == "5"
        assert actual.projects is not None and actual.projects[0].is_favorite is True

    async def test_get_time_tracking_categories(self) -> None:
        payload = {
            "categories": [{"id": "3", "name": "Entwicklung"}],
            "defaultCategoryId": None,
            "isCategoryMandatory": False,
        }
        with aioresponses() as mocked:
            mocked.get(f"{V2}/categories", status=200, payload=payload)
            actual = await make_client().get_time_tracking_categories()
        assert actual == CategoriesResponse.model_validate(payload)
        assert actual.is_category_mandatory is False

    async def test_get_user_profile(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/user/profile", status=200, payload={"id": "42", "role": "MANAGER"})
            actual = await make_client().get_user_profile()
        assert actual.id == "42"
        assert actual.role == "MANAGER"

    async def test_wrong_shape_is_parse_error(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/employees", status=200, payload={"not": "a list"})
            with pytest.raises(TimebutlerParseError):
                await make_client().get_employees()

    async def test_requires_personal_token(self) -> None:
        with pytest.raises(TimebutlerMissingCredentialsError):
            await TimebutlerClient(api_key="k").get_employees()
