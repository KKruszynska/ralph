import numpy as np

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from cycler import cycler

import pyLIMA.fits.objective_functions as pfof
from pyLIMA.outputs.pyLIMA_plots import create_telescopes_to_plot_model
import pyLIMA.outputs.pyLIMA_plots as pyLIMA_plots

from pyLIMA.toolbox import fake_telescopes, plots
from pyLIMA import toolbox as ptool

def define_plotting_dictionaries(telescope_names):
    # Fixed color for each telescope
    # Similar like in pyLIMA
    # Change matplotlib default colors
    n_telescopes = len(telescope_names)
    color = plt.cm.jet(np.linspace(0.01, 0.99, n_telescopes))  # This returns RGBA; convert:
    hexcolor = ['#' + format(int(i[0] * 255), 'x').zfill(2) + format(int(i[1] * 255), 'x').zfill(2) +
                format(int(i[2] * 255), 'x').zfill(2) for i in color]
    # markers
    MARKER_SYMBOLS = np.array(
        [['o', '.', '*', 'v', '^', '<', '>', 's', 'p', 'd', 'x'] * 10]
    )

    marker_cycle = MARKER_SYMBOLS[0][:n_telescopes]
    # color_cycle = cycler.cycler(color=hexcolor)
    # matplotlib.rcParams['axes.prop_cycle'] = cycler.cycler(color=hexcolor)
    color_dict = dict(zip(telescope_names, hexcolor))
    marker_dict = dict(zip(telescope_names, marker_cycle))
    return color_dict, marker_dict

def plot_pyLIMA(event, fit, log):
    """
    Producing plot of the fit, geometry and a corner plot of posteriors for the solution.

    :param event: pyLIMA event, instance of an event for which the fit was performed
    :param fit: pyLIMA fit, instance of a fit

    """
    tel_names = []
    for tel in event.telescopes:
        tel_names.append(tel.name)

    log.info("Fit Analyst: Plots: grabbing colours and markers.")
    color_dict, marker_dict = define_plotting_dictionaries(tel_names)

    custom_color = []
    custom_marker = []

    for tel in event.telescopes:
        custom_color.append(color_dict[tel.name])
        custom_marker.append(marker_dict[tel.name])

    custom_cycler = (cycler(color=custom_color))

    pyLIMA_plots.MARKERS_COLORS = custom_cycler
    pyLIMA_plots.MARKER_SYMBOLS = np.array([custom_marker])

    log.info("Fit Analyst: Starting a plot.")

    fit.fit_outputs(bokeh_plot=True)
    log.info("Fit Analyst: Plotting finished.")

    # try:
    #     fit.fit_outputs(bokeh_plot=True)
    #     log.info("Fit Analyst: Plotting finished.")
    # except Exception as err:
    #     log.error(f"Fit Analyst: %s, %s" % (err, type(err)))
