from __future__ import annotations

from pytest_bdd import scenarios

# Importing the step-def module makes pytest-bdd see every @given/@when/@then
# binding the Delete-Priya feature relies on.
from step_defs.story_1_delete_employee_steps import *  # noqa: F401,F403

scenarios("../features/story_1_delete_employee_priya_sharma.feature")
