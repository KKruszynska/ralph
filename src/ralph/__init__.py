from ._version import __version__
# from .example_module import greetings, meaning

# from .analyst import analyst, analyst_tools, cmd_analyst, event_analyst, light_curve_analyst, fit_analyst
# from .controller import controller
from .fitting_support import fitter
from .fitting_support.pyLIMA import fit_pyLIMA, plots_pyLIMA

__all__ = [
    "fitter",
    "fit_pyLIMA"
    "__version__"
]
