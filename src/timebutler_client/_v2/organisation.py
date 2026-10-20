"""Timebutler API v2: employees, projects, categories, user profile."""

from timebutler_client._v2._http import V2Mixin, parse_model, parse_model_list
from timebutler_client.models.v2 import CategoriesResponse, EmployeeDto, ProjectsResponse, UserProfileResponse


class OrganisationMixin(V2Mixin):
    """Master data visible to the token owner."""

    async def get_employees(self) -> list[EmployeeDto]:
        """
        Fetch employees visible to the token owner (admins: all; managers: their reports and themselves).

        Locked accounts are included with `active=False`. `EmployeeDto.id` matches `employee_id`
        in team absence requests.
        """
        return parse_model_list(EmployeeDto, await self._v2_request("GET", "/employees"))

    async def get_time_tracking_projects(self) -> ProjectsResponse:
        """
        Fetch active projects for time tracking (favourites first), the user's default project and
        whether a project is mandatory. Unlike v1 `get_projects()`, inactive projects are not included.
        """
        return parse_model(ProjectsResponse, await self._v2_request("GET", "/projects"))

    async def get_time_tracking_categories(self) -> CategoriesResponse:
        """Fetch active categories (v1: "services"), the user's default category and whether one is mandatory."""
        return parse_model(CategoriesResponse, await self._v2_request("GET", "/categories"))

    async def get_user_profile(self) -> UserProfileResponse:
        """Fetch the token owner's profile."""
        return parse_model(UserProfileResponse, await self._v2_request("GET", "/user/profile"))
