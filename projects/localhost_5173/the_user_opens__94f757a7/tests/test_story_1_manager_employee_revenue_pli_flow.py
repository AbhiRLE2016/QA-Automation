from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios


_FEATURE = Path(__file__).resolve().parents[1] / "features" / \
    "story_1_manager_employee_revenue_pli_flow.feature"

scenarios(str(_FEATURE))
