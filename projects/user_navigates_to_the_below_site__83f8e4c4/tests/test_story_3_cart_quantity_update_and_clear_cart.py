from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

FEATURE_FILE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "story_3_cart_quantity_update_and_clear_cart.feature"
)

scenarios(str(FEATURE_FILE))
