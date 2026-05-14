import json
import sys

import yaml

from ralph.analyst import analyst_tools
from ralph.analyst.analyst import Analyst
from ralph.analyst.cmd_analyst import CmdAnalyst
from ralph.analyst.fit_analyst import FitAnalyst
from ralph.analyst.light_curve_analyst import LightCurveAnalyst
from ralph.toolbox import input_tools, logs


class EventAnalyst(Analyst):
    """
    A class that analyzes a single event.
    It is a subclass of the :class:`ralph.analyst.analyst.Analyst`
    It coordinates and manages other analysts that handle the analysis of
    the microlensing event (e.g., preprocessing the light curve, fitting
    different microlensing models, creating files with results, event plots,
    and color-magnitude diagrams).

    An Event Analyst needs either a config_path or config_dict, otherwise it will not work.

    :param event_name: A name of the analyzed event.
    :type event_name: str

    :param analyst_path: A path to the folder where the input and output files are saved.
    :type analyst_path: str

    :param log_level: The logging.Logger level (`debug`, `info`, or `error`).
    :type log_level: str

    :param config_dict: A dictionary with Event Analyst configuration.
    :type config_dict: dict, optional

    :param config_path: The path to the configuration file of the Event Analyst.
    :type config_path: str, optional

    :param stream: Flag whether the logging.Logger instance should be available as a stream,
        to be accessible through, for example, Kubernetes.
    :type stream: bool, optional

     Notes on configuration:
    ------------------------------
    The configuration dictionary can contain the following keywords:

    * `event_name`: str
        Event name, mandatory field.
    * `ra`: float
        Right Ascension of the event in degrees.
    * `dec`: float
        Declination of the event in degrees.
    * `lc_analyst`: dict, optional
        A dictionary with Light Curve Analyst configuration,
        see: :class:`ralph.analyst.light_curve_analyst.LightCurveAnalyst`.
    * `fit_analyst`: dict, optional
        A dictionary with Fit Analyst configuration,
        see: :class:`ralph.analyst.fit_analyst.FitAnalyst`.
    * `cmd_analyst`: dict, optional
        A dictionary with CMD Analyst configuration,
        see: :class:`ralph.analyst.cmd_analyst.CMDAnalyst`.
    * `light_curves`: list of dictionaries
        A list of dictionaries with the light curves for the event, mandatory.
        The dictionaries contain the following keywords:
        - `survey`: str
            Name of the survey.
        - `band`: str
            Name of the filter in which the data was taken.
        - `ephemeris`: str, optional
            Path to a file with an ephemeris for a space-based observatory.
        - `path`: str
            Path to a file with the light curve.
    """

    def __init__(
        self,
        event_name,
        analyst_path,
        log_level,
        config_dict=None,
        config_path=None,
        stream=False,
    ):

        super().__init__(event_name, analyst_path, config_dict=config_dict, config_path=config_path)
        self.light_curves = []

        # start
        self.log = logs.start_log(self.analyst_path, log_level, event_name=self.event_name, stream=stream)
        self.log.info("-------------------------------------------")
        self.log.info(f"Event Analyst: Analyzing event {event_name:s}")
        self.log.info("-------------------------------------------")

        if (config_path is not None) or (config_dict is not None):
            if config_path is not None:
                self.parse_config(config_path)

            self.parse_event_config(config_path=config_path, config_dict=config_dict)
        else:
            raise UnboundLocalError(
                "Event Analyst requires a configuration file or a configuration dictionary."
            )

    def parse_event_config(self, config_path=None, config_dict=None):
        """
        Either parses the file or a dictionary with configuration and
        adds it into the internal dictionary of the Event Analyst.

        :param config_path: A path with a YAML or JSON file containing
            the configuration needed for the Event Analyst.
        :type config_path: str

        :param config_dict: A dictionary containing configuration for the Event Analyst.
        :type config_dict: dict
        """

        try:
            if config_path is not None:
                file_format = config_path.split(".")[-1]

                if file_format == "yaml":
                    with open(config_path, "r") as file:
                        event_config = yaml.safe_load(file)
                elif file_format == "json":
                    with open(config_path, "r") as file:
                        event_config = json.load(file)
                        file.close()
            elif config_dict is not None:
                event_config = config_dict

            if "lc_analyst" in event_config:
                self.config["lc_analyst"] = event_config.get("lc_analyst")
                self.log.info("Event Analyst: Light Curve Analyst configuration received.")
            else:
                self.log.info("Event Analyst: No Light Curve Analyst config, it will not be launched.")

            if "fit_analyst" in event_config:
                self.config["fit_analyst"] = event_config.get("fit_analyst")
                self.log.info("Event Analyst: Fit Analyst configuration received.")
            else:
                self.log.info("Event Analyst: No Fit Analyst config, it will not be launched.")

            if "cmd_analyst" in event_config:
                self.config["cmd_analyst"] = event_config.get("cmd_analyst")
                self.log.info("Event Analyst: CMD Analyst configuration received.")
            else:
                self.log.info("Event Analyst: No CMD Analyst config, it will not be launched.")

            self.light_curves = self.parse_light_curves(event_config.get("light_curves"))
            self.log.info("Event Analyst: Light curves received.")

        except Exception as err:
            self.log.error(f"Event Analyst: {err}, {type(err)}")

    def parse_light_curves(self, lc_config):
        """
        Parses the light curve information to be added to the internal dictionary
        of the Event Analyst.

        :param lc_config: A list of dictionaries with the event light curves.
        :type lc_config: list

        :return: a list of dictionaries with the event names, light curves, survey names,
            bands, and, if available, ephemeris.
        :rtype: list
        """
        light_curves = []
        for entry in lc_config:
            survey = entry["survey"]
            band = entry["band"]

            if "path" in entry:
                light_curve = input_tools.load_light_curve_from_path(entry["path"])

                if "ephemeris" in entry:
                    ephemeris = input_tools.load_ephemeris_from_path(
                        entry["ephemeris"],
                        usecols=(0, 1, 2, 3),
                    )

                    light_curves.append(
                        {
                            "light_curve": light_curve,
                            "ephemeris": ephemeris,
                            "survey": survey,
                            "band": band,
                        }
                    )
                    self.log.debug(f"Event Analyst: Loaded light curve with ephemeris for {survey}, {band}.")
                else:
                    light_curves.append(
                        {
                            "light_curve": light_curve,
                            "survey": survey,
                            "band": band,
                        }
                    )
                    self.log.debug(
                        f"Event Analyst: Loaded light curve without ephemeris for {survey}, {band}."
                    )
            else:
                self.log.error("Event Analyst: Problem! No light curve data specified")

        return light_curves

    def run_single_analyst(self):
        """
        Performs tasks assigned to a single Event Analyst. Depending on the configuration it may pass from
        the Light Curve Analyst, to Fit Analyst, to CMD Analyst. All steps are optional.
        The Light Curve Analyst to pre-process the light curves (remove invalid entries).
        The Fit Analyst finds best-fitting microlensing models.
        After fitting is done, output information may be passed to a CMD Analyst,
        that creates a color-magnitude diagram for specified catalogs and plots the source and
        the blend for each found solution.
        """

        self.log.info("Event Analyst: Processing started.")

        if "lc_analyst" in self.config:
            self.run_lc_analyst()

        if "fit_analyst" in self.config:
            self.run_fit_analyst()

        if "cmd_analyst" in self.config:
            self.run_cmd_analyst()

        self.log.info("Event Analyst: Processing finished.")
        self.log.info("-------------------------------------------")
        logs.close_log(self.log)

    def run_lc_analyst(self):
        """
        Launches the Light Curve Analyst to check the quality of the light curve,
        and remove invalid entries.
        """

        self.log.info("Event Analyst: Starting Light Curve Analyst.")
        lc_analyst = LightCurveAnalyst(
            self.event_name, self.analyst_path, self.light_curves, self.log, config_dict=self.config
        )
        self.log.debug("Event Analyst: Light Curve Analyst Created.")
        self.log.debug("Event Analyst: Starting Light Curve quality check.")
        lc_quality_status = lc_analyst.perform_quality_check()
        self.log.debug("Event Analyst: Light Curve quality check ended.")

        if lc_quality_status:
            self.log.info("Event Analyst: Lc quality procedures finished successfully.")
        else:
            self.log.info("Event Analyst: LC Analyst finished with errors.")

    def run_fit_analyst(self):
        """
        Launches the Fit Analyst to find best-fitting microlensing models.
        The Fit Analyst adds a dictionary with all found solitions to
        the internal dictionary of the Event Analyst.
        """

        self.log.info("Event Analyst: Starting Fit Analyst.")
        fit_analyst = FitAnalyst(
            self.event_name, self.analyst_path, self.light_curves, self.log, config_dict=self.config
        )
        self.log.debug("Event Analyst: Fit Analyst created.")
        self.log.debug("Event Analyst: Starting fitting.")
        fit_analyst.perform_fit()
        self.fit_results = fit_analyst.best_results
        self.log.debug("Event Analyst: Fitting finished.")

    def run_cmd_analyst(self):
        """
        Launches the CMD Analyst to create color-magnitude diagrams for all
        specified catalogues and solutions found by the Fit Analyst.
        """

        for dictionary in self.config["cmd_analyst"]["catalogues"]:
            catalogue = dictionary["name"]
            for solution in self.fit_results:
                results = self.fit_results[solution]
                bands = dictionary["band"]

                # gather photometric params
                base, source, blend = {}, {}, {}
                for b in bands:
                    no_total, no_blend = True, True
                    for key in results:
                        if b in key:
                            if "total" in key:
                                no_total = False
                                if "mag_err" in key:
                                    base_err = results[key]
                                elif "mag" in key:
                                    base_mag = results[key]
                            elif "source" in key:
                                if "mag_err" in key:
                                    source_err = results[key]
                                elif "mag" in key:
                                    source_mag = results[key]
                            elif "blend" in key:
                                no_blend = False
                                if "mag_err" in key:
                                    blend_err = results[key]
                                elif "mag" in key:
                                    blend_mag = results[key]

                    source[b] = [source_mag, source_err]

                    if no_blend and no_total:
                        base[b] = [None, None]
                        blend[b] = [None, None]
                    elif no_total and blend_mag is not None:
                        blend[b] = [blend_mag, blend_err]
                        fs, fb = source[b], blend[b]
                        base[b] = analyst_tools.get_baseline_mag(
                            fs[0],
                            fs[1],
                            fb[0],
                            fb[1],
                            self.config["fit_analyst"]["fitting_package"],
                            self.log,
                        )
                    elif no_blend and base_mag is not None:
                        base[b] = [base_mag, base_err]
                        fs, fbase = source[b], base[b]
                        blend[b] = analyst_tools.get_blend_mag(
                            fs[0],
                            fs[1],
                            fbase[0],
                            fbase[1],
                            self.config["fit_analyst"]["fitting_package"],
                            self.log,
                        )
                    else:
                        base[b] = [base_mag, base_err]
                        blend[b] = [blend_mag, blend_err]

                self.log.info(f"Event Analyst: Starting CMD analyst for {catalogue}")
                light_curve_data = {"baseline": base, "source": source, "blend": blend}
                self.log.debug("Event Analyst: Got light curve data.")

                cmd_analyst = CmdAnalyst(
                    self.config["event_name"] + "_" + solution,
                    self.analyst_path,
                    catalogue,
                    light_curve_data,
                    self.log,
                    config_dict=self.config,
                )
                self.log.debug("Event Analyst: CMD Analyst created.")

                source_data = cmd_analyst.transform_source_data()
                self.log.debug("Event Analyst: Finished transforming source data.")

                cmd_data, cmd_labels = cmd_analyst.load_catalogue_data()
                self.log.debug("Event Analyst: Finished loading catalogue data.")

                plot_status = cmd_analyst.plot_cmd(source_data, cmd_data, cmd_labels)
                self.log.debug("Event Analyst: finished creating plot.")
                if plot_status:
                    self.log.info(f"Event Analyst: CMD plot created successfully for {catalogue:s}.")
                else:
                    self.log.error(f"Event Analyst: Problems while creating CMD plot for {catalogue:s}.")


if __name__ == "__main__":
    log_level = ""
    stream = False
    event = ""
    analyst_path = ""
    config_path = ""
    error = False
    error_string = ""

    if "--event_name" in sys.argv:
        idx = sys.argv.index("--event_name")
        event += sys.argv[idx + 1]
    else:
        error = True
        error_string += "Event Analyst: Error! Missing event name!\n"

    if "--analyst_path" in sys.argv:
        idx = sys.argv.index("--analyst_path")
        analyst_path += sys.argv[idx + 1]
    else:
        error = True
        error_string += "Event Analyst: Error! Missing analyst path!\n"

    if "--log_level" in sys.argv:
        idx = sys.argv.index("--log_level")
        log_level += sys.argv[idx + 1]
    else:
        error = True
        error_string += "Event Analyst: Error! Missing log level information!\n"

    if "--stream" in sys.argv:
        idx = sys.argv.index("--stream")
        stream = True if sys.argv[idx + 1] == "True" else False

    if "--config_path" in sys.argv:
        idx = sys.argv.index("--config_path")
        config_path += sys.argv[idx + 1]
        event_analyst = EventAnalyst(event, analyst_path, log_level, config_path=config_path, stream=stream)
    elif "--config_dict" in sys.argv:
        idx = sys.argv.index("--config_dict")
        config = json.loads(sys.argv[idx + 1])
        event_analyst = EventAnalyst(event, analyst_path, log_level, config_dict=config)
    else:
        error = True
        error_string += "Event Analyst: Error! No config specified!"

    if error:
        if (len(log_level) > 0) and (len(analyst_path) > 0):
            log = logs.start_log(analyst_path, log_level, event_name=event, stream=stream)
            log.error("Event Analyst: Error encountered while running an Event Analyst.\n")
            log.error(error_string)
            logs.close_log(log)
        else:
            print("Event Analyst: Error encountered while running an Event Analyst.\n")
            print(error_string)
    else:
        event_analyst.run_single_analyst()
