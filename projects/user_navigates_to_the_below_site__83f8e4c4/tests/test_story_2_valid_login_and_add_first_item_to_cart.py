from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

FEATURE_FILE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "story_2_valid_login_and_add_first_item_to_cart.feature"
)

scenarios(str(FEATURE_FILE))
