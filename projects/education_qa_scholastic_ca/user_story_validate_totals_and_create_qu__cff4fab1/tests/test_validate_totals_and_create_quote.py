from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import scenarios

FEATURE_FILE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "validate_totals_and_create_quote.feature"
)

pytestmark = pytest.mark.validate_totals

scenarios(str(FEATURE_FILE))
