from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import scenarios

FEATURE_FILE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "story_2_cart_quantity_and_clear.feature"
)

pytestmark = pytest.mark.story2

scenarios(str(FEATURE_FILE))
