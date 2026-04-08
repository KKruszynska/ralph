import numpy as np
import pandas as pd
from astroquery.gaia import Gaia

from plotly import graph_objs as go

import os

from MFPipeline.analyst.analyst import Analyst

class CmdAnalyst(Analyst):
    '''
    This is a class that creates a colour-magnitude diagram for one event, one catalogue and one solution.
    It is a child of the :class:`MFPipeline.analyst.analyst.Analyst`

    A CMD Analyst doesn't need config dict, but it needs a self.config already initialized by
    another process.

    :param event_name: str, name of the event
    :param analyst_path: str, path to the folder where the outputs are saved
    :param catalogue: str, name of the catalogue
    :param light_curve_data: dict, dictionary with magnitudes in selected bands for source, blend and baseline; this is a result from fitting.
    :param log: logger instance, log started by Event Analyst
    :param config_dict: dictionary, optional, dictionary with CMD Analyst configuration
    :param config_path: str, optional, path to the YAML configuration file of the CMD Analyst

    Notes on configuration:

    The configuration dictionary can contain the following keywords:

    * `name` str, name of the catalogue
    * `cmd_path` str, optional, path to the catalogue
    * `radius` float, 30 arcmin if not specified, radius of the search of sources in catalogue around the event, used when searching catalogues available through astroquery
    * `optional` dict, a dictionary with optional keywords, used in various places in the code.

    `optional` can contain:

    * `parallax_quality` float, parallax over error constrain demanded for a catalogue search in Gaia catalogues,
    * `separator` str, separator used in the file with the catalogue
    '''
    def __init__(self,
                 event_name,
                 analyst_path,
                 catalogue,
                 light_curve_data,
                 log,
                 config_dict=None,
                 config_path=None):

        Analyst.__init__(self, event_name, analyst_path, config_dict=config_dict, config_path=config_path)
        self.log = log

        if(light_curve_data != None):
            self.light_curve_data = light_curve_data
        else:
            self.log.error("CMD Analyst: Error! CMD Analyst needs source and blend magnitudes.")

        if (config_dict != None):
            self.add_cmd_config(catalogue, config_dict)
        elif ("cmd_analyst" in self.config):
            self.add_cmd_config(catalogue, self.config)
        else:
            self.log.error("CMD Analyst: Error! CMD Analyst needs information.")
            quit()

    def add_cmd_config(self, catalogue, config_dict):
        '''
        Add CMD configuration fields to analyst config.

        :param catalogue: str, catalogue name
        :param config_dict: dict, dictionary with analyst config
        '''

        self.log.debug("CMD Analyst: Adding config.")
        cmd_config = \
            [cat_dict for cat_dict in config_dict["cmd_analyst"]["catalogues"] if cat_dict["name"] == catalogue][0]
        self.catalogue_name = cmd_config.get("name")
        self.radius = cmd_config.get("radius", 30. / 60.)
        self.file_path = cmd_config.get("cmd_path", None)
        self.optional_kwargs = cmd_config.get("optional", None)
        self.log.debug("CMD Analyst: Finished adding config.")
        self.log.debug("CMD Analyst: Added fields: %s,\n %s,\n %s,\n %s"%(self.catalogue_name, self.radius,
                                                        self.file_path, self.optional_kwargs))

    def transform_source_data(self):
        '''
        This function transforms a dictionary (`light_curve_data`) with source, blend and baseline information into two
        data structures, a pandas data frame with magnitudes assuigned in different filter to source, blend and baseline,
        and a list with band labels.

        :return: two data structures, a pandas data frame and band labels.
        '''
        try:
            self.log.debug("CMD Analyst: Creating source and blend mags dataframe and labels.")
            d = []
            l = []
            for key in self.light_curve_data:
                row = [key]
                for inner_key in self.light_curve_data[key]:
                    row.append(self.light_curve_data[key][inner_key])
                    l.append(inner_key)
                d.append(row)
            self.log.debug("CMD Analyst: Collected all labels.")

            labels = l[:len(d[0][:]) - 1]
            cols = ["object"]
            for l in labels:
                cols.append(l)
            data = pd.DataFrame(d, columns=cols)
            self.log.debug("CMD Analyst: Source and blend mags dataframe created.")

        except Exception as err:
            self.log.exception(f"CMD Analyst: %s, %s" % (err, type(err)))
            data = None
            labels = None

        return data, labels

    def load_catalogue_data(self):
        '''
        Loads catalogue data based on the catalogue name, and then selects sources within radius. Either loads
        the catalogue from a file, when `file_path` was specified, or from a selected survey, using astroquery.

        :return: a pandas data frame with data to create a cmd, and a list with band labels
        '''

        self.log.debug("CMD Analyst: Preparing to load the catalogue.")
        if self.file_path is not None:
            if (self.optional_kwargs != None and "separator" in self.optional_kwargs):
                self.log.debug("CMD Analyst: Loading catalogue from file with specified separator.")
                data, labels = self.load_catalogue_from_file_data(separator=self.optional_kwargs["separator"])
            else:
                self.log.debug("CMD Analyst: Loading catalogue from file with default (,) separator.")
                data, labels = self.load_catalogue_from_file_data()
        else:
            self.log.debug("CMD Analyst: Loading catalogue from online catalogues.")
            if "Gaia" in self.catalogue_name:
                if (self.optional_kwargs != None and "parallax_quality" in self.optional_kwargs):
                    self.log.debug("CMD Analyst: Loading catalogue from online catalogue with parallax_quality=%d."%
                                   int(self.optional_kwargs["parallax_quality"]))
                    data, labels = self.load_gaia_data(parallax_quality=self.optional_kwargs["parallax_quality"])
                else:
                    self.log.debug("CMD Analyst: Loading catalogue from online catalogue with \
                                   default parallax_quality=5.")
                    data, labels = self.load_gaia_data()


        return data, labels

    def load_gaia_data(self, parallax_quality=5):
        '''
        Loads data within a specified radius and of specified parallax quality from Gaia catalogues.

        :param catalogue_name: str, specified earlier, should contain words "Gaia" and "DRx", where x is the number of data release (currently supported 1, 2 and 3), for example `GaiaDR2` or `Gaia_DR3`,
        :param radius: float, specified earlier, radius of the search for sources around the event,
        :param parallax_quality: float, optional, parallax over error lower limit.

        :return: pandas data frame with magnitudes and labels of the bands used; the bands are `Gaia_G`, `Gaia_BP`, and `Gaia_RP` corresponding to `phot_g_mean_mag`, `phot_bp_mean_mag` and `phot_rp_mean_mag`.
        '''
        table_name = ""
        if "DR3" in self.catalogue_name:
            table_name = "gaiadr3"
        if "DR2" in self.catalogue_name:
            table_name = "gaiadr2"
        if "DR1" in self.catalogue_name:
            table_name = "gaiadr1"

        self.log.debug("CMD Analyst: Gaia catalogue chosen for %s: %s."%(self.catalogue_name, table_name))

        try:
            if "DR3" in self.catalogue_name:
                adql_query = ("SELECT source_id, phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag \
                                     FROM %s.gaia_source \
                                     WHERE parallax_over_error > %d AND \
                                     ruwe < 1.4 AND \
                                     CONTAINS(POINT(ra, dec), CIRCLE(%f, %f, %f))=1;" %
                              (table_name, int(parallax_quality), self.config["ra"], self.config["dec"], self.radius))
            else:
                adql_query = ("SELECT source_id, phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag \
                             FROM %s.gaia_source \
                             WHERE parallax_over_error > %d \
                             CONTAINS(POINT(ra, dec), CIRCLE(%f, %f, %f))=1;"%
                              (table_name, int(parallax_quality), self.config["ra"], self.config["dec"], self.radius))

            self.log.debug("CMD Analyst: Querying Gaia.")
            self.log.debug("CMD Analyst: Query:\n %s"%adql_query)
            Gaia.load_tables(only_names=True)
            job = Gaia.launch_job_async(adql_query)
            result = job.get_results()
            self.log.debug("CMD Analyst: Query response retrieved.")

            data = {"Gaia_G" : result["phot_g_mean_mag"],
                    "Gaia_BP" : result["phot_bp_mean_mag"],
                    "Gaia_RP" : result["phot_rp_mean_mag"]
                    }
            data_frame = pd.DataFrame(data=data)
            labels = ["Gaia_G", "Gaia_BP", "Gaia_RP"]
            self.log.debug("CMD Analyst: Response reformatted to dataframe, labels created.")

        except Exception as err:
            self.log.exception(f"CMD Analyst: %s, %s" % (err, type(err)))
            data_frame = None
            labels = None

        return data_frame, labels

    def load_catalogue_from_file_data(self, separator=","):
        '''
        Loads a file with catalogue data from path specified by the user in the configuration.

        :return: pandas data frame and labels of the bands
        '''

        try:
            self.log.debug("CMD Analyst: Attempting to read the data from file.")
            data = pd.read_csv(self.file_path, sep=separator)
            labels = data.columns.tolist()
            self.log.debug("CMD Analyst: Data loaded to dataframe, labels created.")

        except Exception as err:
            self.log.exception(f"CMD Analyst: %s, %s" % (err, type(err)))
            data = None
            labels = None

        return data, labels


    def plot_cmd(self, source_data, source_labels, cmd_data, cmd_labels):
        '''
        Create a colour magnitude diagram with magnitudes obtained from fitting plotted on it.

        :param source_data: pandas dataframe with magnitudes obtained from fitting microlensing model
        :param source_labels: labels of filters of magnitude in the `source_data`
        :param cmd_data: pandas data frame with magnitudes of the sources around the event coming from a survey
        :param cmd_labels: labels of filters in the `cmd_data`

        :return: status of creating a cmd plot
        '''

        self.log.debug("CMD Analyst: Plotting CMD started.")
        for i in range(len(cmd_labels)):
            self.log.debug("CMD Analyst: Plotting CMD for labels: %s"%cmd_labels[i])
            colours = {"baseline": "#000000",  # black
                       "source": "#E69F00",  # orange
                       "blend": "#56B4E9",  # sky blue
                       "bluish_green": "#009E73",  # blueish green
                       "yellow": "#F0E442",  # yellow
                       "blue": "#0072B2",  # blue
                       "vermillon": "D55E00",  # vermillon
                       "reddish_purple": "#CC79A7"}  # reddish_purple Wong colour palette, https://www.nature.com/articles/nmeth.1618
            try:
                fig = go.Figure()

                fig.add_trace(go.Scatter(x=cmd_data[cmd_labels[1]] - cmd_data[cmd_labels[2]],
                                         y=cmd_data[cmd_labels[i]],
                                         mode="markers",
                                         marker=dict(
                                             color="grey",
                                             size=5,
                                             opacity=0.5, ),
                                         name=self.catalogue_name,
                                         showlegend=True
                                         ), )
                self.log.debug("CMD Analyst: Catalogue data plotted.")

                for j in range(len(source_data["object"].values[:])):
                    if source_data[cmd_labels[1]].iloc[j][0] is None:
                        continue

                    fig.add_trace(
                        go.Scatter(x=[source_data[cmd_labels[1]].iloc[j][0] - source_data[cmd_labels[2]].iloc[j][0]],
                                   y=[source_data[cmd_labels[i]].iloc[j][0]],
                                   error_x=dict(
                                       type="data", # value of error bar given in data coordinates
                                       array=[np.sqrt(source_data[cmd_labels[1]].iloc[j][1] ** 2 + source_data[cmd_labels[2]].iloc[j][1]** 2)],
                                       visible=True),
                                   error_y=dict(
                                       type="data",  # value of error bar given in data coordinates
                                       array=[[source_data[cmd_labels[i]].iloc[j][1]]],
                                       visible=True),
                                   mode="markers",
                                   marker=dict(
                                       color=colours[source_data["object"].iloc[j]],
                                       size=10,
                                   ),
                                   name=source_data["object"].iloc[j],
                                   showlegend=True
                                   ), )
                    self.log.debug("CMD Analyst: Plotted data for %s."%source_data['object'].iloc[j])

                fig.update_layout(
                    title="%s CMD" % self.event_name,
                    title_x=0.5,
                    xaxis_title="%s - %s" % (cmd_labels[1], cmd_labels[2]),
                    yaxis_title=cmd_labels[i],
                    legend_title="Legend",
                    font=dict(
                        family="arial",
                        size=18,
                        color="black"
                    ),
                    width=600,
                    height=600,
                    yaxis=dict(autorange="reversed"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                self.log.debug("CMD Analyst: Title, legend and axes titles created.")

                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
                fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor="lightgray")
                self.log.debug("CMD Analyst: Grid added.")

                os.makedirs("./"+self.analyst_path, exist_ok=True)
                fig.write_html(
                    "%s/%s_CMD_%s_%s.html" % ("./"+self.analyst_path, self.event_name, self.catalogue_name, cmd_labels[i])
                    )
                self.log.debug("CMD Analyst: Plot saved.")

                cmd_status = True

            except Exception as err:
                self.log.exception(f"CMD Analyst: %s, %s" % (err, type(err)))
                cmd_status = False

        return cmd_status