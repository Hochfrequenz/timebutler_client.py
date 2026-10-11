"""Async client for the Timebutler API (v1 and v2)."""

from pydantic import BaseModel, PrivateAttr

from timebutler_client._v1 import V1_BASE_URL, V1Mixin
from timebutler_client._v2._http import V2_BASE_URL, V2Transport
from timebutler_client._v2.organisation import OrganisationMixin


class TimebutlerClient(V1Mixin, OrganisationMixin, BaseModel):
    """
    Async client for the Timebutler API.

    v1 (API key, company-wide CSV exports) and v2 (personal token, JSON, acts as the token owner)
    can be used independently or together.

    Example:
        client = TimebutlerClient(api_key="your-api-key")
        absences = await client.get_absences(year=2026)

        client = TimebutlerClient(personal_token="tb_...")
        entries = await client.get_my_time_entries(year=2026, month=10)
    """

    base_url: str = V1_BASE_URL
    base_url_v2: str = V2_BASE_URL
    timeout: float = 30.0
    _api_key: str | None = PrivateAttr(default=None)
    _v2: V2Transport | None = PrivateAttr(default=None)

    def __init__(
        self,
        api_key: str | None = None,
        personal_token: str | None = None,
        base_url: str = V1_BASE_URL,
        base_url_v2: str = V2_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        api_key = api_key.strip() if api_key and api_key.strip() else None
        personal_token = personal_token.strip() if personal_token and personal_token.strip() else None
        if api_key is None and personal_token is None:
            raise ValueError("At least one of api_key or personal_token must be provided")
        super().__init__(base_url=base_url, base_url_v2=base_url_v2, timeout=timeout)
        self._api_key = api_key
        if personal_token is not None:
            self._v2 = V2Transport(base_url=base_url_v2, timeout=timeout, access_token=personal_token)

    def __repr__(self) -> str:
        return (
            f"TimebutlerClient(base_url={self.base_url!r}, base_url_v2={self.base_url_v2!r}, "
            f"api_key={'****' if self._api_key else None}, personal_token={'****' if self._v2 else None})"
        )

    @classmethod
    async def from_password(
        cls,
        username: str,
        password: str,
        *,
        client_id: str = "public",
        client_secret: str | None = None,
        api_key: str | None = None,
        base_url: str = V1_BASE_URL,
        base_url_v2: str = V2_BASE_URL,
        timeout: float = 30.0,
    ) -> "TimebutlerClient":
        """
        Create a client by logging in with username/password (OAuth password grant).

        The access token is refreshed automatically on 401. Accounts with 2FA cannot use this;
        create a personal token instead.
        """
        transport = await V2Transport.password_login(
            base_url=base_url_v2,
            timeout=timeout,
            username=username,
            password=password,
            client_id=client_id,
            client_secret=client_secret,
        )
        client = cls(
            api_key=api_key,
            personal_token=transport.access_token,
            base_url=base_url,
            base_url_v2=base_url_v2,
            timeout=timeout,
        )
        client._v2 = transport
        return client
