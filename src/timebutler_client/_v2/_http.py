"""HTTP transport for the Timebutler API v2 (JSON, bearer auth)."""

from timebutler_client.exceptions import TimebutlerMissingCredentialsError

V2_BASE_URL = "https://app.timebutler.com/api/v2"


class V2Transport:
    """Holds v2 credentials and performs authenticated requests."""

    def __init__(
        self,
        base_url: str,
        timeout: float,
        access_token: str,
        refresh_token: str | None = None,
        client_id: str = "public",
        client_secret: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret


class V2Mixin:
    """Base for all v2 area mixins. Mixed into TimebutlerClient."""

    _v2: V2Transport | None

    def _require_v2(self) -> V2Transport:
        if self._v2 is None:
            raise TimebutlerMissingCredentialsError("personal_token")
        return self._v2
