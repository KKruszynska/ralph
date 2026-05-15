import matplotlib.pyplot as plt
import numpy as np
import pyLIMA.outputs.pyLIMA_plots as pyLIMA_plots
from cycler import cycler


def define_plotting_dictionaries(telescope_names):
    """
    Defines plotting dictionaries with telescopes having
    consistent markers and colors.

    :param telescope_names: list of telescope names
    :type telescope_names: list

    :return: Dictionaries with telescope name and assigned color (color_dict),
        and telescope name and assigned marker (marker_dict).
    :rtype: dict
    """
    # Fixed color for each telescope
    # Similar like in pylima
    # Change matplotlib default colors
    n_telescopes = len(telescope_names)
    color = plt.cm.jet(np.linspace(0.01, 0.99, n_telescopes))  # This returns RGBA; convert:
    hexcolor = [
        "#"
        + format(int(i[0] * 255), "x").zfill(2)
        + format(int(i[1] * 255), "x").zfill(2)
        + format(int(i[2] * 255), "x").zfill(2)
        for i in color
    ]
    # markers
    marker_symbols = np.array([["o", ".", "*", "v", "^", "<", ">", "s", "p", "d", "x"] * 10])

    marker_cycle = marker_symbols[0][:n_telescopes]
    color_dict = dict(zip(telescope_names, hexcolor, strict=False))
    marker_dict = dict(zip(telescope_names, marker_cycle, strict=False))
    return color_dict, marker_dict


def plot_pylima(event, fit, log):
    """
    Produces plot of the best-fitting model, its geometry and a corner plot of
    the posterior parameter probability distribution.

    :param event: A pyLIMA event instance.
    :type event: pyLIMA.event.Event

    :param fit: A pyLIMA fit instance.
    :type fit: pyLIMA.fits.ML_fit or its subclass

    :param log: A logger instance initialized by the Event Analyst,
        to which the logs will be written.
    :type log: logging.Logger
    """
    plt.close('all')

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

    custom_cycler = cycler(color=custom_color)

    pyLIMA_plots.MARKERS_COLORS = custom_cycler
    pyLIMA_plots.MARKER_SYMBOLS = np.array([custom_marker])

    log.info("Fit Analyst: Starting a plot.")

    fit.fit_outputs(bokeh_plot=True)
    log.info("Fit Analyst: Plotting finished.")

    plt.close('all')
