from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

FEATURE_FILE = Path(__file__).resolve().parents[1] / "features" / "saucedemo_checkout.feature"

scenarios(str(FEATURE_FILE))
