import yaml


class Analyst:
    """
    This is a class that analyzes one event.
    This class creates bare bones of other analysts and contains elements they all share.

    :param event_name: str, name of the analyzed event
    :param ra: float, Right Ascention of the analyzed event
    :param dec: float, declination of the analyzed event
    :param analyst_path: str, path to the folder where the outputs are saved
    :param config_dict: dictionary, optional, dictionary with Analyst configuration
    :param config_path: str, optional, path to the YAML configuration file of the Analyst
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

    def parse_config(self, config_path):
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
            with open(config_path, "r") as file:
                event_config = yaml.safe_load(file)

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
        This function swaps minuses in name to underscores, to avoid problems for some operating systems.

        :param name: str, name or path to be updated
        :return: str, updated name without minuses
        """

        updated_name = name.replace(" ", "_").replace("-", "_")

        return updated_name
