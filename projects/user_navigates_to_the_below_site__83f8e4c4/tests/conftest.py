from __future__ import annotations

# Step-def modules are wildcard-imported so pytest-bdd registers every
# @given/@when/@then before scenario collection.
from step_defs.common_steps import *  # noqa: F401,F403
from step_defs.storefront_steps import *  # noqa: F401,F403
