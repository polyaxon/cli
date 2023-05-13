from clipped.decorators.deprecation import warn_deprecation

from polyaxon import pkg

warn_deprecation(
    current_version=pkg.VERSION,
    deprecation_version="2.0.0",
    latest_version="2.1.0",
    current_logic="from polyaxon.polytune.search_managers.bayesian_optimization import BayesSearchManager",
    new_logic="from polyaxon.tuners.bayesian_optimization import GridSearchManager",
    details="Please the new `polyaxon.tuners` module.",
)

from hypertune.search_managers.bayesian_optimization.manager import BayesSearchManager
