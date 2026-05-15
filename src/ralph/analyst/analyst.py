import yaml
import json

class BaseAnalyst:
    """
    This is a base Analyst class.
    This class creates bare bones of other analysts and contains elements they all share.

    :param event_name: A name of the analyzed event.
    :type event_name: str

    :param analyst_path: A path to the folder where the input and output files are saved.
    :type analyst_path: str

    :param config_dict: A dictionary with Base Analyst configuration.
    :type config_dict: dict, optional

    :param config_path: The path to the configuration file of the Base Analyst.
    :type config_path: str, optional

    Notes on configuration:
    ------------------------------
    The configuration dictionary has to contain the following keywords:

    * `event_name`: str
        Event name.
    * `ra`: float
        Right Ascension of the event in degrees.
    * `dec`: float
        Declination of the event in degrees.
    """

    def __init__(self, event_name, analyst_path, config_dict=None, config_path=None):

        self.event_name = self.update_names_paths(event_name)
        self.analyst_path = self.update_names_paths(analyst_path)

        if (config_path is not None) or (config_dict is not None):
            self.config = self.parse_config(config_path=config_path, config_dict=config_dict)
        else:
            raise UnboundLocalError(
                    "The Analyst requires a configuration file or a configuration dictionary"
                )

    def parse_config(self, config_path=None, config_dict=None):
        """
        Either parses the file or a dictionary with configuration and
        returns it as a dictionary.

        :param config_path: A path with a YAML or JSON file containing
            the configuration needed for the Base Analyst.
        :type config_path: str

        :param config_dict: A dictionary containing configuration for the Base Analyst.
        :type config_dict: dict

        :return: A configuration dictionary with basic information.
        :rtype: dict
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

            config = {
                "event_name": event_config.get("event_name"),
                "ra": float(event_config.get("ra")),
                "dec": float(event_config.get("dec")),
            }

            return config

        except Exception as err:
            print(f"Unexpected {err}, {type(err)}")

    def update_names_paths(self, name):
        """
        Swaps minuses and blank spaces in name to underscores, to avoid problems
        for some operating systems.

        :param name: A name or path to be updated.
        :type name: str

        :return: An updated name or path without unsafe characters.
        :rtype: str
        """

        updated_name = name.replace(" ", "_").replace("-", "_")

        return updated_name
