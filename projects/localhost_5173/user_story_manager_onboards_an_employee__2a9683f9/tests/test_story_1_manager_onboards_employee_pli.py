from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

FEATURE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "story_1_manager_onboards_employee_pli.feature"
)

scenarios(str(FEATURE))
