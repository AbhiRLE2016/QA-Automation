from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenarios

# Bind every Scenario in the feature file to a pytest test. The matching
# step-defs are registered via tests/conftest.py importing the step module.
_FEATURE = (
    Path(__file__).resolve().parents[1]
    / "features"
    / "story_1_create_organization_relevance_lab.feature"
)

scenarios(str(_FEATURE))
