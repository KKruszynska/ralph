import pandas as pd
from MFPipeline import logs

scenario_file = {
        "path_input" : "tests/test_cmd/input/gdr3-ulens-025_result.csv",
        "separator" : ",",
        "path_outputs": "tests/test_cmd/output/",
        "event_name": "GDR3-ULENS-025",
        "ra": 260.8781,
        "dec": -27.3788,
        "catalogue_name": "Gaia_DR3",
        "catalogue_bands" : ["Gaia_G", "Gaia_BP", "Gaia_RP"],
        "light_curve_data": {
            "baseline": {
                "Gaia_G": 16.12,
                "Gaia_BP": 17.78,
                "Gaia_RP": 14.88
            },
            "source": {
                "Gaia_G": 16.14,
                "Gaia_BP": 17.79,
                "Gaia_RP": 14.91
            },
            "blend": {
                "Gaia_G": 20.37,
                "Gaia_BP": 22.78,
                "Gaia_RP": 18.69
                },
            }
}

scenario_gaia = {
        "path_outputs": "tests/test_cmd/output",
        "event_name": "GDR3-ULEN-025",
        "ra": 260.8781,
        "dec": -27.3788,
        "catalogue_name": "Gaia_DR3",
        "catalogue_bands" : ["Gaia_G", "Gaia_BP", "Gaia_RP"],
        "light_curve_data": {
            "baseline": {
                "Gaia_G": 16.12,
                "Gaia_BP": 17.78,
                "Gaia_RP": 14.88
            },
            "source": {
                "Gaia_G": 16.14,
                "Gaia_BP": 17.79,
                "Gaia_RP": 14.91
            },
            "blend": {
                "Gaia_G": 20.37,
                "Gaia_BP": 22.78,
                "Gaia_RP": 18.69
                },
            }
}

class testCmdAnalyst():
    '''
    Class with tests
    '''
    def __init__(self,
                 scenario):
        self.scenario = scenario

    def test_plot_gaia(self):
        from MFPipeline.analyst.cmd_analyst import CmdAnalyst

        config = {}
        config["event_name"] = self.scenario.get("event_name")
        config["ra"], config["dec"] = self.scenario.get("ra"), self.scenario.get("dec")

        cats = []

        catalogue = self.scenario.get("catalogue_name")
        path_outputs = self.scenario.get("path_outputs")
        catalogue_bands = self.scenario.get("catalogue_bands")
        light_curve_data = self.scenario.get("light_curve_data")

        if self.scenario.get("path_input") is not None:
            sep = self.scenario.get("separator")
            path_input = self.scenario.get("path_input")
            dict = {
                "name": catalogue,
                "band": catalogue_bands,
                "cmd_path": path_input,
                "separator": sep,
                }
        else:
            dict = {
                "name": catalogue,
                "band": catalogue_bands,
                }

        cats.append(dict)
        config["cmd_analyst"] = {}
        config["cmd_analyst"]["catalogues"] = cats
        log = logs.start_log(path_outputs, 'debug', event_name=config["event_name"], stream=True)
        analyst = CmdAnalyst(config["event_name"], path_outputs, catalogue, light_curve_data, log, config_dict=config)

        source_data, source_labels = analyst.transform_source_data()
        cmd_data, cmd_labels = analyst.load_catalogue_data()
        plot_status = analyst.plot_cmd(source_data, source_labels, cmd_data, cmd_labels)
        logs.close_log(log)

        # assert plot_status == True


    def test_load_gaia(self):
        from MFPipeline.analyst.cmd_analyst import CmdAnalyst

        config = {}
        config["event_name"] = self.scenario.get("event_name")
        config["ra"], config["dec"] = self.scenario.get("ra"), self.scenario.get("dec")

        cats = []

        catalogue = self.scenario.get("catalogue_name")
        path_outputs = self.scenario.get("path_outputs")
        catalogue_bands = self.scenario.get("catalogue_bands")
        light_curve_data = self.scenario.get("light_curve_data")

        if self.scenario.get("path_input") is not None:
            sep = self.scenario.get("separator")
            path_input = self.scenario.get("path_input")
            dict = {
                "name": catalogue,
                "band": catalogue_bands,
                "cmd_path": path_input,
                "separator": sep,
            }
        else:
            dict = {
                "name": catalogue,
                "band": catalogue_bands,
            }

        cats.append(dict)
        config["cmd_analyst"] = {}
        config["cmd_analyst"]["catalogues"] = cats
        log = logs.start_log(path_outputs, 'debug', event_name=config["event_name"], stream=True)
        analyst = CmdAnalyst(config["event_name"], path_outputs, catalogue, light_curve_data, log, config_dict=config)

        cmd_data, cmd_labels = analyst.load_catalogue_data()

        logs.close_log(log)

        assert type(cmd_data) == pd.DataFrame
        assert type(cmd_labels) == list

    def test_load_source_gaia(self):
        from MFPipeline.analyst.cmd_analyst import CmdAnalyst

        config = {}
        config["event_name"] = self.scenario.get("event_name")
        config["ra"], config["dec"] = self.scenario.get("ra"), self.scenario.get("dec")

        cats = []

        catalogue = self.scenario.get("catalogue_name")
        path_outputs = self.scenario.get("path_outputs")
        catalogue_bands = self.scenario.get("catalogue_bands")
        light_curve_data = self.scenario.get("light_curve_data")

        if self.scenario.get("path_input") is not None:
            sep = self.scenario.get("separator")
            path_input = self.scenario.get("path_input")
            dict = {
                "name": catalogue,
                "band": catalogue_bands,
                "cmd_path": path_input,
                "separator": sep,
            }
        else:
            dict = {
                "name": catalogue,
                "band": catalogue_bands,
            }

        cats.append(dict)
        config["cmd_analyst"] = {}
        config["cmd_analyst"]["catalogues"] = cats
        log = logs.start_log(path_outputs, 'debug', event_name=config["event_name"])
        analyst = CmdAnalyst(config["event_name"], path_outputs, catalogue, light_curve_data, log, config_dict=config)

        source_data, source_labels = analyst.transform_source_data()

        logs.close_log(log)

        assert type(source_data) ==  pd.DataFrame
        assert type(source_labels) ==  list

def test_run():
    case = scenario_file
    test = testCmdAnalyst(case)
    test.test_load_source_gaia()
    test.test_load_gaia()
    test.test_plot_gaia()

    # for case in [scenario_file, scenario_gaia]:
    #     test = testCmdAnalyst(case)
    #     test.test_load_source_gaia()
    #     test.test_load_gaia()
    #     test.test_plot_gaia()

