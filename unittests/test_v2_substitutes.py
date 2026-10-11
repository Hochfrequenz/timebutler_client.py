"""Tests for v2 substitute endpoints."""

from aioresponses import aioresponses

from unittests.v2_helpers import V2, make_client


class TestSubstitutes:
    """/substitute-employees, /substitute-requests*"""

    async def test_all(self) -> None:
        with aioresponses() as mocked:
            mocked.get(f"{V2}/substitute-employees", status=200, payload=[{}])
            mocked.get(f"{V2}/substitute-requests", status=200, payload=[{}, {}])
            mocked.get(f"{V2}/substitute-requests/pending-count", status=200, payload={})
            mocked.post(f"{V2}/substitute-requests/4/accept", status=200, payload={})
            mocked.post(f"{V2}/substitute-requests/4/reject", status=200, payload={})
            client = make_client()
            assert len(await client.get_substitute_employees()) == 1
            assert len(await client.get_substitute_requests()) == 2
            await client.get_substitute_requests_pending_count()
            await client.accept_substitute_request("4")
            await client.reject_substitute_request(4)
            assert sum(len(calls) for calls in mocked.requests.values()) == 5
