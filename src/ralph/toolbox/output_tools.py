import numpy as np

from bokeh.plotting import figure, output_file, save

def plot_outlier_results(
        plot_location,
        plot_name,
        lc,
        outlier_results,
        outlier_sequence
):
    """
    Plot outlier results for a single light curve (`plot_name`)
    using bokeh plotting library, and then save it as an HTML file
    at a location specified by `plot_location`. Outliers are flagged
    during the
    :meth:`ralph.analyst.light_curve_analyst.LightCurveAnalyst.perform_outlier_check`

    :param plot_location: Location where the plot will be saved.
    :type plot_location: str

    :param plot_name: Name of the plot, effectively survey name and light curve band.
    :type plot_name: str

    :param lc: Light curve for which outliers were flagged.
    :type lc: numpy array

    :param outlier_results: A dictionary with outlier flagging resylts.
        Contains four numpy arrays, see:
        :meth:`ralph.analyst.light_curve_analyst.LightCurveAnalyst.hampel_filter`.
    :type outlier_results: dict

    :param outlier_sequence: A list of dictionaries with found outlier sequences,
        see :meth:`ralph.analyst.light_curve_analyst.LightCurveAnalyst.vet_outliers`.
    :type outlier_sequence: dict
    """

    outliers = outlier_results["is_outlier"]
    medians = outlier_results["medians"]
    thresholds = outlier_results["thresholds"]

    output_file(filename=plot_location, title=f"Outliers for {plot_name}")

    p = figure(title="Outliers found by the Hampel filter",
               x_axis_label="JD", y_axis_label="mag",
               width=1000, height=800)

    p.varea(x=lc[:,0],
            y1=medians + thresholds,
            y2=medians - thresholds,
            fill_color="grey",
            alpha=0.5,
            legend_label="Medians +/- thresholds",
            )

    mag_plot = np.linspace(np.min(lc[:,1]), np.max(lc[:,1]), 10)

    for sequence in outlier_sequence:
        t_start = sequence["t_start"]
        t_end = sequence["t_end"]

        p.harea(x1=t_start,
                x2=t_end,
                y=mag_plot)

        p.vspan(
            x=[t_start, t_end],
            line_width=[2, 2], line_color="cornflowerblue",
        )

    p.scatter(lc[:,0], lc[:,1],
              legend_label=f"Cleaned {plot_name}",
              marker="circle",
              color="#DB8C1D", size=8)

    # create the coordinates for the errorbars
    err_xs = []
    err_ys = []

    for x, y, yerr in zip(lc[:,0], lc[:,1], lc[:,2]):
        err_xs.append((x, x))
        err_ys.append((y - yerr, y + yerr))

    # plot them
    p.multi_line(err_xs, err_ys, color='#DB8C1D')

    p.scatter(lc[outliers,0], lc[outliers,1],
              legend_label=f"Outliers",
              marker="x",
              color="navy", size=8)

    p.y_range.flipped = True

    p.legend.location = "top_left"

    save(p)
