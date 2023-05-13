from clipped.decorators.deprecation import warn_deprecation

from polyaxon import pkg

warn_deprecation(
    current_version=pkg.VERSION,
    deprecation_version="2.0.0",
    latest_version="2.1.0",
    current_logic="from polyaxon.polytune.search_managers.grid_search import GridSearchManager",
    new_logic="from polyaxon.tuners.grid_search import GridSearchManager",
    details="Please the new `polyaxon.tuners` module.",
)

from hypertune.search_managers.grid_search.manager import GridSearchManager
