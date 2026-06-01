from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

# Bind every scenario in the feature file to this test module.
_FEATURE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "story_1_all_employees_directory_walk.feature"
)

scenarios(str(_FEATURE))
