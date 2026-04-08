import numpy as np
import yaml
import json
import sys
import time

from MFPipeline.analyst.analyst import Analyst

from MFPipeline.analyst.light_curve_analyst import LightCurveAnalyst
from MFPipeline.analyst.fit_analyst import FitAnalyst
from MFPipeline.analyst.cmd_analyst import CmdAnalyst

from MFPipeline import logs
from MFPipeline.analyst import analyst_tools


class EventAnalyst(Analyst):
    """
    This is a class that analyzes one event.
    It is a child of the :class:`MFPipeline.analyst.analyst.Analyst`
    It takes care of other sub-analysts that fit microlensing models to the light curve,
    create colour-magnitude diagrams and perform other additional tasks.

    An Event Analyst needs either a config_path or config_dict, otherwise it will not work.

    :param event_name: str, name of the analyzed event
    :param analyst_path: str, path to the folder where the outputs are saved
    :param log_level: str, level of logging
    :param config_dict: dictionary, optional, dictionary with Event Analyst configuration
    :param config_path: str, optional, path to the YAML configuration file of the Event Analyst
    :param stream: optional, boolean, should the log be accessible through Kubernetes?
    """

    def __init__(self,
                 event_name,
                 analyst_path,
                 log_level,
                 config_dict=None,
                 config_path=None,
                 stream=False,
                 ):

        super().__init__(event_name, analyst_path, config_dict=config_dict, config_path=config_path)
        # Analyst.__init__(self, event_name, analyst_path, config_dict=config_dict, config_path=config_path)
        self.light_curves = []

        # start
        self.log = logs.start_log(self.analyst_path, log_level, event_name=self.event_name, stream=stream)
        self.log.info("-------------------------------------------")
        self.log.info("Event Analyst: Analyzing event {:s}".format(event_name))
        self.log.info("-------------------------------------------")

        if config_path is not None:
            self.parse_config(config_path)
            self.parse_event_config(config_path)
        elif config_dict is not None:
            self.add_config_dict(config_dict)
        else:
            self.log.error("Event Analyst: Error! Event Analyst needs information.")
            quit()

    def parse_event_config(self, config_path):
        """
        Parse YAML file with configuration, turn it into a dictionary and to

        :param config_path: str, path with YAML file containing additional information needed for an Event Analyst.
        """

        try:
            file_format = config_path.split(".")[-1]

            if file_format == "yaml":
                with open(config_path, 'r') as file:
                    event_config = yaml.safe_load(file)
            elif file_format == "json":
                with open(config_path, 'r') as file:
                    event_config = json.load(file)
                    file.close()

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

        except Exception as err:
            self.log.error(f"Event Analyst: %s, %s" % (err, type(err)))

    def add_config_dict(self, conifg_dict):
        """
        Adds sections of config relevant to Event Analyst to its configuration file.

        :param conifg_dict: dict, dictionary containing configuration for Event Analyst

        """

        try:
            self.light_curves = self.parse_light_curves(conifg_dict.get("light_curves"))

            if "lc_analyst" in conifg_dict:
                self.config["lc_analyst"] = conifg_dict.get("lc_analyst")
                self.log.info("Event Analyst: Light Curve Analyst configuration received.")
            else:
                self.log.info("Event Analyst: No Light Curve Analyst config, it will not be launched.")

            if "fit_analyst" in conifg_dict:
                self.config["fit_analyst"] = conifg_dict.get("fit_analyst")
                self.log.info("Event Analyst: Fit Analyst configuration received.")
            else:
                self.log.info("Event Analyst: No Fit Analyst config, it will not be launched.")

            if "cmd_analyst" in conifg_dict:
                self.config["cmd_analyst"] = conifg_dict.get("cmd_analyst")
                self.log.info("Event Analyst: CMD Analyst configuration received.")
            else:
                self.log.info("Event Analyst: No CMD Analyst config, it will not be launched.")

        except Exception as err:
            self.log.error(f"Event Analyst: %s, %s" % (err, type(err)))

    def parse_light_curves(self, lc_config):
        """
        This function parses the light curve information.
        :param lc_config: dictionary with light curves specified for the event
        :return: a list with event names, light curves, survey names, bands
        """
        light_curves = []
        for entry in lc_config:
            survey = entry["survey"]
            band = entry["band"]
            if "path" in entry:
                light_curve = np.genfromtxt(entry["path"], unpack=True)
                light_curves.append({
                    "lc": light_curve,
                    "survey": survey,
                    "band": band
                })
            elif "lc" in entry:
                if type(entry["lc"]) == type([1,1]):
                    light_curve = entry["lc"]
                else:
                    light_curve = json.loads(entry["lc"])
                light_curves.append({
                    "lc": light_curve,
                    "survey": survey,
                    "band": band
                })
            else:
                self.log.error("Event Analyst: Problem! No light curve data specified")

        return light_curves

    def run_single_analyst(self):
        """
        Perform tasks assigned to a single Event Analyst. First the event is handled by a Fit Analyst, searching
        for fitting microlensing models. After fitting is done, output information is passed to a CMD Analyst, that
        creates a CMD plot for specified catalogs and plots the source and blend for each found solution.

        :return: status?
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
        Launch Light Curve Analyst to check the quality of the light curve.
        Placeholder.
        """

        lc_quality_status = False

        self.log.info("Event Analyst: Starting Light Curve Analyst.")
        lc_analyst = LightCurveAnalyst(self.event_name, self.analyst_path, self.light_curves,
                                       self.log,
                                       config_dict=self.config
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
        Launch Fit Analyst to find all fitting microlensing events.
        """

        self.log.info("Event Analyst: Starting Fit Analyst.")
        fit_analyst = FitAnalyst(self.event_name, self.analyst_path, self.light_curves,
                                 self.log,
                                 config_dict=self.config
                                 )
        self.log.debug("Event Analyst: Fit Analyst created.")
        self.log.debug("Event Analyst: Starting fitting.")
        fit_analyst.perform_fit()
        self.fit_results = fit_analyst.best_results
        self.log.debug("Event Analyst: Fitting finished.")

    def run_cmd_analyst(self):
        """
        Launch CMD Analyst to create a CMD plot for all solutions and specified catalogues.

        :return: a list of boolean values corresponding to status of the created cmd plots.
        """
        cmd_plot_status = []

        for dictionary in self.config["cmd_analyst"]["catalogues"]:
            catalogue = dictionary["name"]
            for solution in self.fit_results:
                results = self.fit_results[solution]
                bands = analyst_tools.cmd_catalogues_to_bands(catalogue)

                # gather photometric params
                base, source, blend = {}, {}, {}
                for b in bands:
                    no_total, no_blend = True, True
                    for i, key in enumerate(results):
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
                        base[b] = analyst_tools.get_baseline_mag(fs[0], fs[1], fb[0], fb[1],
                                                                 self.config["fit_analyst"]["fitting_package"],
                                                                 self.log)
                    elif no_blend and base_mag is not None:
                        base[b] = [base_mag, base_err]
                        fs, fbase = source[b], base[b]
                        blend[b] = analyst_tools.get_blend_mag(fs[0], fs[1], fbase[0], fbase[1],
                                                               self.config["fit_analyst"]["fitting_package"],
                                                               self.log)
                    else:
                        base[b] = [base_mag, base_err]
                        blend[b] = [blend_mag, blend_err]


                self.log.info("Event Analyst: Starting CMD analyst for %s" % catalogue)
                light_curve_data = {'baseline': base,
                                    'source': source,
                                    'blend': blend}
                self.log.debug("Event Analyst: Got light curve data.")

                cmd_analyst = CmdAnalyst(self.config["event_name"]+"_"+solution, self.analyst_path, catalogue, light_curve_data,
                                         self.log,
                                         config_dict=self.config
                                         )
                self.log.debug("Event Analyst: CMD Analyst created.")

                source_data, source_labels = cmd_analyst.transform_source_data()
                self.log.debug("Event Analyst: Finished transforming source data.")

                cmd_data, cmd_labels = cmd_analyst.load_catalogue_data()
                self.log.debug("Event Analyst: Finished loading catalogue data.")

                plot_status = cmd_analyst.plot_cmd(source_data, source_labels, cmd_data, cmd_labels)
                self.log.debug("Event Analyst: finished creating plot.")
                if plot_status:
                    self.log.info("Event Analyst: CMD plot created successfully for {:s}.".format(catalogue))
                else:
                    self.log.error("Event Analyst: Problems while creating CMD plot for %s.".format(catalogue))


if __name__ == "__main__":
    log_level = ""
    stream = False
    event = ""
    analyst_path = ""
    config_path = ""
    error = False
    error_string = ""
    print("============================= Hello!!")

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
        if sys.argv[idx + 1] == "True":
            stream = True,
        else:
            stream = False

    if "--config_path" in sys.argv:
        idx = sys.argv.index("--config_path")
        config_path += sys.argv[idx + 1]
        event_analyst = EventAnalyst(event, analyst_path, log_level,
                                     config_path=config_path,
                                     stream=stream
                                     )
    elif "--config_dict" in sys.argv:
        idx = sys.argv.index("--config_dict")
        config = json.loads(sys.argv[idx + 1])
        event_analyst = EventAnalyst(event, analyst_path, log_level,
                                     config_dict=config
                                     )
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
