"""Tests that the generated v2 models are up to date and behave as expected."""

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from timebutler_client.models.v2 import TimeEntryDto

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestGeneratedModels:
    """Checks on models/v2/_generated.py."""

    def test_aliases_and_snake_case(self) -> None:
        entry = TimeEntryDto.model_validate({"id": "1", "workedMinutes": 480, "autoStopped": False})
        assert entry.worked_minutes == 480
        assert entry.auto_stopped is False

    def test_models_are_frozen(self) -> None:
        entry = TimeEntryDto.model_validate({"id": "1"})
        with pytest.raises(ValidationError):
            entry.id = "2"

    def test_unknown_fields_are_ignored(self) -> None:
        entry = TimeEntryDto.model_validate({"id": "1", "somethingNew": 42})
        assert entry.id == "1"

    @pytest.mark.skipif(
        importlib.util.find_spec("datamodel_code_generator") is None, reason="codegen group not installed"
    )
    def test_generated_file_matches_spec(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        try:
            import generate_v2_models  # type: ignore[import-not-found]  # noqa: PLC0415
        finally:
            sys.path.pop(0)
        output = tmp_path / "_generated.py"
        generate_v2_models.generate(output)
        expected = (REPO_ROOT / "src" / "timebutler_client" / "models" / "v2" / "_generated.py").read_text(
            encoding="utf-8"
        )
        assert output.read_text(encoding="utf-8") == expected, "Run scripts/generate_v2_models.py and commit the result"
