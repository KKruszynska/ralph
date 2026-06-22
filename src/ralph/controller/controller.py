import json
import os
import subprocess

import yaml

from ralph.toolbox import logs
from ralph.toolbox.custom_process_pool_excecutor import RalphPoolExecutor


class Controller:
    """
    This is a class that controls other analysts and their corresponding tasks.
    A controller has to be initialized with either config_path or config_dict specified.
    Otherwise, it will not work.

    :param event_list: A list with names of events that will be analyzed by the pipeline.
    :type event_list: list

    :param config_path: A path to a JSON or a YAML file that has the configuration
        parameters for the Controller.
    :type config_path: str, optional

    :param config_dict: A dictionary containing configuration of the Controller.
    :type config_dict: dict, optional

    :param analyst_dicts: A dictionary containing configuration dictionaries with information
        for the Analysts.
    :type analyst_dicts: dict, optional

    :param stream: If set to `True`, the log will be streamed to the standard output,
            and then can be captured with, for example, Kubernetes; if set to `False`,
            the log will be saved to the location specified in `log_location` Controller configuration parameter.
    :type stream: bool, optional

    Notes on configuration:
    ------------------------------
    The configuration dictionary can contain the following keywords:

        * `python_compiler` - name of the Python interpreter; `python` will use the default interpreter,
            `python3.x` will use specific version of the interpreter, or it can be a path to
            Virtual Environment's Python compiler;
        * `group_processing_limit` - how many events will be analyzed at the same time; it is limited by
            how many cores are available;
        * `config_type` - file format (YAML or JSON) used for your configuration files for the Event Analysts;
        * `events_path` - a path to the outputs save locations, and where Event Analysts should look for
            the configuration files for each event;
        * `software_dir` - the path to `Ralph`'s repository location of the Analysts' source files;
        * `log_stream` - if `log_stream` is set to `True`, the log will be streamed to the standard output,
            if set to `False`, the log will be saved to the location specified in `log_location`;
        * `log_location` - path to save location of the Controller logs; the file will appear in
            the `log_location` directory, under the name `controller.log`;
        * `log_level` - how verbose should the log statements be; there are three levels available:
            `error` (least verbose), `info` (medium), `debug` (very verbose).
    """

    def __init__(self, event_list, config_path=None, config_dict=None, analyst_dicts=None):

        self.event_list = event_list
        self.analyst_dicts = analyst_dicts

        if config_dict is not None:
            # READ config_dict
            self.config = config_dict


            self.log = logs.start_log(
                self.config["log_location"],
                self.config["log_level"],
                event_name=None,
                stream=self.config["log_stream"]
            )

            self.log.info("Processing started. Opened log.")

        elif config_path is not None:
            # read config path
            self.config_path = config_path
            self.config = self.parse_config()
        else:
            raise UnboundLocalError(
                "Controller requires a configuration file or a configuration dictionary."
            )

    def parse_config(self):
        """
        Function that parses the YAML or json file with configuration.

        :return: configuration in form of a dictionary.
        """

        config = {}
        try:
            file_format = self.config_path.split(".")[-1]

            if file_format == "yaml":
                with open(self.config_path, "r") as file:
                    controller_config = yaml.safe_load(file)
            elif file_format == "json":
                with open(self.config_path, "r") as file:
                    controller_config = json.load(file)
                    file.close()

            config["events_path"] = controller_config.get("events_path")
            config["software_dir"] = controller_config.get("software_dir")
            config["python_compiler"] = controller_config.get("python_compiler")
            config["group_processing_limit"] = controller_config.get("group_processing_limit")
            config["config_type"] = controller_config.get("config_type")
            config["log_location"] = controller_config.get("log_location")
            config["log_level"] = controller_config.get("log_level")
            if "log_stream" in controller_config:
                config["log_stream"] = controller_config.get("log_stream")

        except Exception as err:
            self.log.exception(f"Controller: {err}, {type(err)}")
            config = None

        return config

    @staticmethod
    def run_parallel_analyst(command):
        """
        Run a single analyst as a subprocess.

        :param command: A command to be executed by subprocess.
        :type command: list
        """
        subprocess.run(command, shell=False)

    def launch_analysts(self):
        """
        This function starts and parallelizes the :class:`ralph.analyst.event_analyst.EventAnalyst`.
        """

        self.log.info("Controller: Start processing.")
        # First create all the commands to run the analysts
        commands = []
        self.log.debug("Controller: Creating the commands to launch analysts.")
        for event in self.event_list:
            command = [
                self.config["python_compiler"],
                os.path.join(self.config["software_dir"], "event_analyst.py"),
                "--event_name",
                event,
                "--analyst_path",
                os.path.join(self.config["events_path"],  event + "/"),
                "--log_level",
                self.config["log_level"],
            ]

            if "log_stream" in self.config:
                command.append("--stream")
                command.append(str(self.config["log_stream"]))

            if self.analyst_dicts is not None:
                self.log.debug("Controller: Analyst dicts specified.")
                command.append("--config_dict")
                command.append(str(self.analyst_dicts[event]))
            else:
                self.log.debug("Controller: Analyst dicts not specified, \
                    will look for information in their config files.")
                command.append("--config_path")
                command.append(
                    os.path.join(self.config['events_path'], event, f"config.{self.config['config_type']}")
                )

            commands.append(command)

        # Running analysts in batches
        self.log.info("Controller: Commands created. Spawning processes.")
        self.log.debug(f"Controller: Max workers set as: {self.config['group_processing_limit']:d}")

        max_cores = os.cpu_count()
        if self.config["group_processing_limit"] > max_cores:
            max_workers = max_cores
            self.log.info(f"Controller: Max workers exceeded maximum available cores: {max_cores}")
            self.log.info(f"Controller: Group_processing_limit set to {max_cores}")
        else:
            max_workers = self.config["group_processing_limit"]

        with RalphPoolExecutor(max_workers=max_workers, logger=self.log) as executor:
            self.log.debug("Controller: New process spawned.")
            list(executor.map(self.run_parallel_analyst, commands))

        self.log.info("Controller: Processing finished.")
        logs.close_log(self.log)


