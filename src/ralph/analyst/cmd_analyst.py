import os

import numpy as np
import pandas as pd
from plotly import graph_objs as go

from ralph.analyst.analyst import BaseAnalyst


class CmdAnalyst(BaseAnalyst):
    """
    This is a class that creates a color-magnitude diagram for one event, one catalogue
    and one solution.
    It is a subclass of the :class:`ralph.analyst.analyst.BaseAnalyst`

    A CMD Analyst doesn't need config dict, but it needs a self.config already initialized by
    another process.

    :param event_name: The name of the event.
    :type event_name: string

    :param analyst_path: The path to the folder where the outputs are saved.
    :type analyst_path: string

    :param catalogue:  The name of the catalogue used for building the color-magnitude diagram.
    :type catalogue: string

    :param light_curve_data:  A dictionary with magnitudes in selected bands for source, baseline,
     and, if available, blend. This is a result from running the Fit Analyst.
    :type light_curve_data: dict

    :param log: A logger instance started by the Event Analyst.
    :type log: logging.Logger

    :param config_dict: A dictionary with the Event Analyst configuration.
    :type config_dict: dict, optional

    :param config_path: A path to the configuration file of the Event Analyst.
    :type config_path: string, optional

    Notes on configuration:
    ------------------------------
    The configuration dictionary can contain the following keywords:

    * `name`: string
        The name of the catalogue.
    * `cmd_path`: string
        The path to the catalogue.
    * `separator`: string
        A separator used in the file with the catalogue.
    """

    def __init__(self, event_name, analyst_path, catalogue,
                 light_curve_data, log, config_dict=None,
                 config_path=None
    ):

        super().__init__(event_name, analyst_path, config_dict=config_dict, config_path=config_path)
        self.log = log

        self.catalogue_name = None
        self.file_path = None
        self.separator = None

        if light_curve_data is not None:
            self.light_curve_data = light_curve_data
        else:
            self.log.error("CMD Analyst: Error! CMD Analyst needs at least source and baseline magnitudes.")

        if config_dict is not None:
            self.add_cmd_config(catalogue, config_dict)
        elif "cmd_analyst" in self.config:
            self.add_cmd_config(catalogue, self.config)
        else:
            self.log.error("CMD Analyst: Error! CMD Analyst needs configuration parameters.")
            quit()

    def add_cmd_config(self, catalogue, config_dict):
        """
        Adds configuration fields to the internal CMD Analyst configuration dictionary.

        :param catalogue: The name of the catalogue.
        :type catalogue: string

        :param config_dict: A dictionary with the Event Analyst configuration.
        :type config_dict: dict
        """

        self.log.debug("CMD Analyst: Adding config.")
        cmd_config = [
            cat_dict for cat_dict in config_dict["cmd_analyst"]["catalogues"] if cat_dict["name"] == catalogue
        ][0]
        self.catalogue_name = cmd_config.get("name")
        self.file_path = cmd_config.get("cmd_path", None)
        self.separator = cmd_config.get("separator", ",")
        self.log.debug("CMD Analyst: Finished adding config.")
        self.log.debug(f"CMD Analyst: Added fields: {self.catalogue_name},\n\
                       {self.file_path},\n {self.separator},\n")

    def transform_source_data(self):
        """
        Transforms a dictionary (`light_curve_data`) with source, blend and
        baseline information into a Pandas DataFrame with magnitudes assigned in different
        filters to source, blend and baseline.

        :return: A DataFrame with magnitudes assigned in different filters to source,
                 blend and baseline.
        :rtype: pandas.DataFrame
        """
        try:
            self.log.debug("CMD Analyst: Creating source and blend mags dataframe and labels.")
            dataframe = []
            labs = []
            for key in self.light_curve_data:
                row = [key]
                for inner_key in self.light_curve_data[key]:
                    row.append(self.light_curve_data[key][inner_key])
                    labs.append(inner_key)
                dataframe.append(row)
            self.log.debug("CMD Analyst: Collected all labels.")

            labels = labs[: len(dataframe[0][:]) - 1]
            cols = ["object"]
            for lab in labels:
                cols.append(lab)
            data = pd.DataFrame(dataframe, columns=cols)
            self.log.debug("CMD Analyst: Source and blend mags dataframe created.")

        except Exception as err:
            self.log.exception(f"CMD Analyst: {err}, {type(err)}")
            data = None

        return data

    def load_catalogue_data(self):
        """
        Loads catalogue data based on the catalogue names.
        It loads the catalogue from a file.

        :return: A data frame with data to create a color-magnitude diagram, and a list with band labels.
        :rtype: pandas.DataFrame, list
        """

        self.log.debug("CMD Analyst: Preparing to load the catalogue.")
        if self.file_path is not None:
            if self.separator is not None:
                self.log.debug(
                    f"CMD Analyst: Loading catalogue from file with specified separator: {self.separator}"
                )
                data, labels = self.load_catalogue_from_file_data(separator=self.separator)
            else:
                self.log.debug(
                    f"CMD Analyst: Loading catalogue from file with default separator: {self.separator}"
                )
                data, labels = self.load_catalogue_from_file_data()
        else:
            self.log.error("CMD Analyst: Missing path to CMD data.")

        return data, labels

    def load_catalogue_from_file_data(self, separator=","):
        """
        Loads a file with catalogue data from path specified by the user in the configuration.

        :param separator: A separator used in the file with the data.
        :type separator: string, optional

        :return: pandas data frame and labels of the bands
        """

        try:
            self.log.debug("CMD Analyst: Attempting to read the data from file.")
            data = pd.read_csv(self.file_path, sep=separator)
            labels = data.columns.tolist()
            self.log.debug("CMD Analyst: Data loaded to dataframe, labels created.")

        except Exception as err:
            self.log.exception(f"CMD Analyst: {err}, {type(err)}")
            data = None
            labels = None

        return data, labels

    def plot_cmd(self, source_data, cmd_data, cmd_labels):
        """
        Create a color-magnitude diagram based on catalog data and the source, baseline, and,
        if available, blend of a selected model and its best-fitting solution. The resulting
        plot is saved as an HTML file.

        :param source_data: A dataframe with source, baseline, (and blend) magnitudes obtained
            for a selected model and its best-fitting solution.
        :type source_data: pandas.DataFrame

        :param cmd_data: A dataframe with catalog data of the nearby sources, coming from the survey.
        :type cmd_data: pandas.DataFrame

        :param cmd_labels: A list with labels of filters used by the `cmd_data` and `source_data`.
        :type cmd_labels: list

        :return: status of the plot creation, `True` if created sucessfully, `False` otherwise.
        :rtype: bool
        """

        self.log.debug("CMD Analyst: Plotting CMD started.")
        for i in range(len(cmd_labels)):
            self.log.debug(f"CMD Analyst: Plotting CMD for labels: {cmd_labels[i]}")

            #  Wong colour palette, https://www.nature.com/articles/nmeth.1618
            colours = {
                "baseline": "#000000",  # black
                "source": "#E69F00",  # orange
                "blend": "#56B4E9",  # sky blue
                "bluish_green": "#009E73",  # blueish green
                "yellow": "#F0E442",  # yellow
                "blue": "#0072B2",  # blue
                "vermilion": "D55E00",  # vermilion
                "reddish_purple": "#CC79A7",
            }  # reddish_purple
            try:
                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=cmd_data[cmd_labels[1]] - cmd_data[cmd_labels[2]],
                        y=cmd_data[cmd_labels[i]],
                        mode="markers",
                        marker=dict(
                            color="grey",
                            size=5,
                            opacity=0.5,
                        ),
                        name=self.catalogue_name,
                        showlegend=True,
                    ),
                )
                self.log.debug("CMD Analyst: Catalogue data plotted.")

                for j in range(len(source_data["object"].values[:])):
                    if source_data[cmd_labels[1]].iloc[j][0] is None:
                        continue

                    fig.add_trace(
                        go.Scatter(
                            x=[source_data[cmd_labels[1]].iloc[j][0] - source_data[cmd_labels[2]].iloc[j][0]],
                            y=[source_data[cmd_labels[i]].iloc[j][0]],
                            error_x=dict(
                                type="data",  # value of error bar given in data coordinates
                                array=[
                                    np.sqrt(
                                        source_data[cmd_labels[1]].iloc[j][1] ** 2
                                        + source_data[cmd_labels[2]].iloc[j][1] ** 2
                                    )
                                ],
                                visible=True,
                            ),
                            error_y=dict(
                                type="data",  # value of error bar given in data coordinates
                                array=[[source_data[cmd_labels[i]].iloc[j][1]]],
                                visible=True,
                            ),
                            mode="markers",
                            marker=dict(
                                color=colours[source_data["object"].iloc[j]],
                                size=10,
                            ),
                            name=source_data["object"].iloc[j],
                            showlegend=True,
                        ),
                    )
                    self.log.debug(f"CMD Analyst: Plotted data for {source_data['object'].iloc[j]}")

                fig.update_layout(
                    title=f"{self.event_name} CMD",
                    title_x=0.5,
                    xaxis_title=f"{cmd_labels[1]} - {cmd_labels[2]}",
                    yaxis_title=cmd_labels[i],
                    legend_title="Legend",
                    font=dict(family="arial", size=18, color="black"),
                    width=600,
                    height=600,
                    yaxis=dict(autorange="reversed"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                self.log.debug("CMD Analyst: Title, legend and axes titles created.")

                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
                fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor="lightgray")
                self.log.debug("CMD Analyst: Grid added.")

                os.makedirs("./" + self.analyst_path, exist_ok=True)
                fig.write_html(
                    f"./{self.analyst_path}/{self.event_name}_CMD_{self.catalogue_name}_{cmd_labels[i]}.html"
                )
                self.log.debug("CMD Analyst: Plot saved.")

                cmd_status = True

            except Exception as err:
                self.log.exception(f"CMD Analyst: {err}, {type(err)}")
                cmd_status = False

        return cmd_status
