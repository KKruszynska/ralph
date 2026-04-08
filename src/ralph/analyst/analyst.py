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
    def __init__(self,
                 event_name,
                 analyst_path,
                 config_dict=None,
                 config_path=None):

        self.event_name = self.update_names_paths(event_name)
        self.analyst_path = self.update_names_paths(analyst_path)

        self.config = {}
        if (config_dict != None):
            # READ config_dict
            self.config = config_dict
        elif (config_path != None):
            # read config path
            self.parse_config(config_path)
        else:
            # todo: raise custom exception here?
            print("Error! Analyst needs information!!!")
            quit()

    def parse_config(self, config_path):
        """
        Parse YAML file with configuration, turn it into a dictionary and add it to self.

        :param config_path: str, path with YAML file containing Analyst configuration.
        """

        config = {}
        try:
            with open(config_path, 'r') as file:
                event_config = yaml.safe_load(file)

            self.config["event_name"] = event_config.get("event_name")
            self.config["ra"] = float(event_config.get("ra"))
            self.config["dec"] = float(event_config.get("dec"))

        except Exception as err:
            print(f"Unexpected %s, %s" % (err, type(err)))

    def update_names_paths(self, name):
        """
        This function swaps minuses in name to underscores, to avoid problems for some operating systems.

        :param name: str, name or path to be updated
        :return: str, updated name without minuses
        """

        updated_name = name.replace(" ", "_").replace("-", "_")

        return updated_name

