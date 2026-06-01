from __future__ import annotations

from pytest_bdd import scenarios

# Import the step-def modules so pytest-bdd registers every step phrase used
# in the Delete-Priya feature (the new story reuses the prior story's shared
# phrases such as `Given the user opens "..."` and the password-fill steps,
# plus the new DELTA matchers appended to story_1_delete_employee_steps.py).
from step_defs.story_1_delete_employee_steps import *  # noqa: F401,F403
from step_defs.story_1_verify_all_employees_against_csv_steps import *  # noqa: F401,F403

scenarios("../features/story_1_delete_employee_priya_sharma.feature")
