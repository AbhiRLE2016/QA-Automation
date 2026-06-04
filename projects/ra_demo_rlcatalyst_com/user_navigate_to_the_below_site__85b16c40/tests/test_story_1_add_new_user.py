from __future__ import annotations

import pytest
from pytest_bdd import scenarios

# Registering the step-def module so pytest-bdd discovers @given/@when/@then
# defined in step_defs/story_1_add_new_user_steps.py.
from step_defs import story_1_add_new_user_steps  # noqa: F401

pytestmark = pytest.mark.story1

scenarios("../features/story_1_add_new_user.feature")
