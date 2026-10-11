"""Every operation in the pinned v2 OpenAPI spec must have a client method."""

import json
from pathlib import Path

from timebutler_client import TimebutlerClient

SPEC = Path(__file__).resolve().parent.parent / "spec" / "timebutler-v2-openapi.json"

OPERATIONS: dict[tuple[str, str], str] = {
    ("POST", "/oauth2/token"): "from_password",
    ("GET", "/absence-requests"): "get_my_absence_requests",  # alias of /absence-requests/my
    ("GET", "/absence-requests/my"): "get_my_absence_requests",
    ("GET", "/absence-requests/team"): "get_team_absence_requests",
    ("GET", "/absence-requests/pending-count"): "get_absence_requests_pending_count",
    ("POST", "/absence-requests"): "create_absence_request",
    ("PUT", "/absence-requests/{id}"): "update_absence_request",
    ("DELETE", "/absence-requests/{id}"): "delete_absence_request",
    ("POST", "/absence-requests/{id}/approve"): "approve_absence_request",
    ("POST", "/absence-requests/{id}/reject"): "reject_absence_request",
    ("GET", "/absence-types"): "get_absence_types",
    ("GET", "/cancellation-requests"): "get_cancellation_requests",
    ("GET", "/cancellation-requests/pending-count"): "get_cancellation_requests_pending_count",
    ("POST", "/cancellation-requests/{id}/approve"): "approve_cancellation_request",
    ("POST", "/cancellation-requests/{id}/reject"): "reject_cancellation_request",
    ("GET", "/categories"): "get_time_tracking_categories",
    ("GET", "/employees"): "get_employees",
    ("GET", "/projects"): "get_time_tracking_projects",
    ("GET", "/user/profile"): "get_user_profile",
    ("GET", "/substitute-employees"): "get_substitute_employees",
    ("GET", "/substitute-requests"): "get_substitute_requests",
    ("GET", "/substitute-requests/pending-count"): "get_substitute_requests_pending_count",
    ("POST", "/substitute-requests/{id}/accept"): "accept_substitute_request",
    ("POST", "/substitute-requests/{id}/reject"): "reject_substitute_request",
    ("GET", "/time-clock/status"): "get_time_clock_status",
    ("POST", "/time-clock/start"): "start_time_clock",
    ("POST", "/time-clock/pause"): "pause_time_clock",
    ("POST", "/time-clock/resume"): "resume_time_clock",
    ("POST", "/time-clock/stop"): "stop_time_clock",
    ("POST", "/time-clock/cancel"): "cancel_time_clock",
    ("POST", "/time-clock/business-trip-start"): "start_business_trip",
    ("POST", "/time-clock/business-trip-end"): "end_business_trip",
    ("GET", "/time-entries/my"): "get_my_time_entries",
    ("GET", "/time-entries/pending-count"): "get_time_entries_pending_count",
    ("DELETE", "/time-entries/{id}"): "delete_time_entry",
    ("POST", "/time-tracking/clock-entry"): "create_time_entry",
    ("GET", "/time-tracking/work-summary"): "get_work_summary",
    ("GET", "/time-tracking/time-off-summary"): "get_time_off_summary",
    ("GET", "/time-entry-requests"): "get_time_entry_requests",
    ("POST", "/time-entry-requests/{id}/approve"): "approve_time_entry_request",
    ("POST", "/time-entry-requests/{id}/reject"): "reject_time_entry_request",
}


class TestSpecCoverage:
    """Spec <-> client mapping."""

    def test_every_spec_operation_is_mapped(self) -> None:
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        in_spec = {
            (method.upper(), path)
            for path, ops in spec["paths"].items()
            for method in ops
            if method in {"get", "post", "put", "delete", "patch"}
        }
        assert in_spec == set(OPERATIONS), f"unmapped: {in_spec - set(OPERATIONS)}, stale: {set(OPERATIONS) - in_spec}"

    def test_every_mapped_method_exists(self) -> None:
        for name in OPERATIONS.values():
            assert callable(getattr(TimebutlerClient, name, None)), name
