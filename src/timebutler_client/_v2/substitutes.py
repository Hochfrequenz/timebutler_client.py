"""Timebutler API v2: substitutes."""

from timebutler_client._v2._http import V2Mixin, parse_model, parse_model_list, path_id
from timebutler_client.models.v2 import SubstituteEmployeeDto, SubstitutePendingCountResponse, SubstituteRequestDto


class SubstitutesMixin(V2Mixin):
    """Substitute employees and substitute requests addressed to the token owner."""

    async def get_substitute_employees(self) -> list[SubstituteEmployeeDto]:
        """Employees the token owner can choose as substitute."""
        return parse_model_list(SubstituteEmployeeDto, await self._v2_request("GET", "/substitute-employees"))

    async def get_substitute_requests(self) -> list[SubstituteRequestDto]:
        """Substitute requests addressed to the token owner."""
        return parse_model_list(SubstituteRequestDto, await self._v2_request("GET", "/substitute-requests"))

    async def get_substitute_requests_pending_count(self) -> SubstitutePendingCountResponse:
        """Number of open substitute requests."""
        data = await self._v2_request("GET", "/substitute-requests/pending-count")
        return parse_model(SubstitutePendingCountResponse, data)

    async def accept_substitute_request(self, request_id: int | str) -> SubstituteRequestDto:
        """Accept a substitute request."""
        data = await self._v2_request("POST", f"/substitute-requests/{path_id(request_id)}/accept")
        return parse_model(SubstituteRequestDto, data)

    async def reject_substitute_request(self, request_id: int | str) -> SubstituteRequestDto:
        """Reject a substitute request."""
        data = await self._v2_request("POST", f"/substitute-requests/{path_id(request_id)}/reject")
        return parse_model(SubstituteRequestDto, data)
