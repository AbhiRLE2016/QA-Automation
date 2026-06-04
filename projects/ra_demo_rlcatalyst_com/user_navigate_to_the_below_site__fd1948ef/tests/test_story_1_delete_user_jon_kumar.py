from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import scenarios

FEATURE_FILE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "story_1_delete_user_jon_kumar.feature"
)

pytestmark = pytest.mark.story1

scenarios(str(FEATURE_FILE))
