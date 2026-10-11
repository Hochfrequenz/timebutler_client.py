"""Tests for credential handling of TimebutlerClient."""

import pytest

from timebutler_client import TimebutlerClient, TimebutlerMissingCredentialsError


class TestCredentials:
    """Constructor and credential checks."""

    def test_requires_at_least_one_credential(self) -> None:
        with pytest.raises(ValueError, match="api_key or personal_token"):
            TimebutlerClient()

    def test_positional_api_key_still_works(self) -> None:
        client = TimebutlerClient("legacy-key")
        assert client.base_url == "https://app.timebutler.com/api/v1"

    def test_personal_token_only(self) -> None:
        client = TimebutlerClient(personal_token="tb_abc")
        assert client.base_url_v2 == "https://app.timebutler.com/api/v2"

    def test_personal_token_is_stripped(self) -> None:
        client = TimebutlerClient(personal_token="  tb_abc\n")
        assert client._require_v2().access_token == "tb_abc"  # pylint: disable=protected-access

    def test_blank_personal_token_counts_as_missing(self) -> None:
        with pytest.raises(ValueError):
            TimebutlerClient(personal_token="   ")

    def test_repr_masks_both_credentials(self) -> None:
        text = repr(TimebutlerClient(api_key="secret-key", personal_token="tb_secret"))
        assert "secret-key" not in text
        assert "tb_secret" not in text

    async def test_v1_method_without_api_key_raises(self) -> None:
        client = TimebutlerClient(personal_token="tb_abc")
        with pytest.raises(TimebutlerMissingCredentialsError) as excinfo:
            await client.get_projects()
        assert excinfo.value.credential == "api_key"

    def test_v2_without_token_raises(self) -> None:
        client = TimebutlerClient(api_key="key")
        with pytest.raises(TimebutlerMissingCredentialsError) as excinfo:
            client._require_v2()  # pylint: disable=protected-access
        assert excinfo.value.credential == "personal_token"
