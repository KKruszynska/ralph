import pandas as pd
import os
from pathlib import Path

from ralph.analyst.cmd_analyst import CmdAnalyst
from ralph.toolbox import logs

scenario_file = {
        'path_input' : 'tests/ralph/data/input/cmd/gdr3_ulens_025_result.csv',
        'separator' : ',',
        'path_outputs': 'tests/ralph/data/output/cmd_analyst/',
        'event_name': 'GDR3_ULENS_025',
        'ra': 260.8781,
        'dec': -27.3788,
        'catalogue_name': 'Gaia_DR3',
        'catalogue_bands' : ['Gaia_G', 'Gaia_BP', 'Gaia_RP'],
        'light_curve_data': {
            'baseline': {
                'Gaia_G': [16.12, 0.01, 0.01],
                'Gaia_BP': [17.78, 0.01, 0.02],
                'Gaia_RP': [14.88, 0.01, 0.02],
            },
            'source': {
                'Gaia_G': [16.14,  0.01, 0.01],
                'Gaia_BP': [17.79, 0.02, 0.02],
                'Gaia_RP': [14.91, 0.01, 0.02],
            },
            'blend': {
                'Gaia_G': [20.37, 0.01, 0.01],
                'Gaia_BP': [22.78, 0.02, 0.02],
                'Gaia_RP': [18.69, 0.01, 0.02],
                },
            }
}

# scenario_gaia = {
#         'path_outputs': 'tests/test_cmd/output',
#         'event_name': 'GDR3_ULEN_025',
#         'ra': 260.8781,
#         'dec': -27.3788,
#         'catalogue_name': 'Gaia_DR3',
#         'catalogue_bands' : ['Gaia_G', 'Gaia_BP', 'Gaia_RP'],
#         'light_curve_data': {
#             'baseline': {
#                 'Gaia_G': 16.12,
#                 'Gaia_BP': 17.78,
#                 'Gaia_RP': 14.88
#             },
#             'source': {
#                 'Gaia_G': 16.14,
#                 'Gaia_BP': 17.79,
#                 'Gaia_RP': 14.91
#             },
#             'blend': {
#                 'Gaia_G': 20.37,
#                 'Gaia_BP': 22.78,
#                 'Gaia_RP': 18.69
#                 },
#             }
# }

class CmdAnalystTest:
    """
    Class with tests.
    """

    def __init__(self,
                 scenario):
        self.scenario = scenario

    def load_scenario(self):
        """
        Load test scenario file.
        """

        config = {
            'event_name': self.scenario.get('event_name'),
            'ra': self.scenario.get('ra'),
            'dec': self.scenario.get('dec'),
        }

        cats = []

        catalogue = self.scenario.get('catalogue_name')
        path_outputs = self.scenario.get('path_outputs')
        catalogue_bands = self.scenario.get('catalogue_bands')
        light_curve_data = self.scenario.get('light_curve_data')

        if self.scenario.get('path_input') is not None:
            sep = self.scenario.get('separator')
            path_input = self.scenario.get('path_input')
            config_dict = {
                'name': catalogue,
                'band': catalogue_bands,
                'cmd_path': path_input,
                'separator': sep,
            }
        else:
            config_dict = {
                'name': catalogue,
                'band': catalogue_bands,
            }

        cats.append(config_dict)
        config['cmd_analyst'] = {
            'catalogues': cats
        }

        return config, path_outputs, light_curve_data

    def test_plot_gaia(self):
        """
        Test if plots are created.
        """

        config, path_outputs, light_curve_data = self.load_scenario()
        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'])
        analyst = CmdAnalyst(config['event_name'], path_outputs,
                             config['cmd_analyst']['catalogues'][0]['name'],
                             light_curve_data,
                             log, config_dict=config)

        source_data, source_labels = analyst.transform_source_data()
        cmd_data, cmd_labels = analyst.load_catalogue_data()
        plot_status = analyst.plot_cmd(source_data, source_labels, cmd_data, cmd_labels)
        logs.close_log(log)

        # assert if plot exists at expected location
        assert plot_status

        event_name = config['event_name']
        catalogue_name =  config['cmd_analyst']['catalogues'][0]['name']
        cmd_labels = self.scenario.get('catalogue_bands')

        for band in cmd_labels:
            output = Path(f'./{path_outputs}/{event_name}_CMD_{catalogue_name}_{band}.html')
            assert output.exists() is True
            assert output.is_file() is True

    def test_load_gaia(self):
        """
        Check if data is loaded correctly.
        """

        config, path_outputs, light_curve_data = self.load_scenario()
        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'])
        analyst = CmdAnalyst(config['event_name'], path_outputs,
                             config['cmd_analyst']['catalogues'][0]['name'],
                             light_curve_data,
                             log, config_dict=config
                             )

        cmd_data, cmd_labels = analyst.load_catalogue_data()

        logs.close_log(log)

        assert type(cmd_data) is pd.DataFrame
        assert type(cmd_labels) is list

    def test_load_source_gaia(self):
        """
        Check if source information is loaded correctly.
        """

        config, path_outputs, light_curve_data = self.load_scenario()
        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'])
        analyst = CmdAnalyst(config['event_name'], path_outputs,
                             config['cmd_analyst']['catalogues'][0]['name'],
                             light_curve_data,
                             log, config_dict=config
                             )

        source_data, source_labels = analyst.transform_source_data()

        logs.close_log(log)

        assert type(source_data) is  pd.DataFrame
        assert type(source_labels) is  list

def test_run():
    """
    Run all tests.
    """
    case = scenario_file
    test = CmdAnalystTest(case)
    test.test_load_source_gaia()
    test.test_load_gaia()
    test.test_plot_gaia()

    # for case in [scenario_gaia, scenario_gsa]:
    analyst_path = case.get('path_outputs')
    event_name = case.get('event_name')
    print(analyst_path, event_name)
    output = Path(analyst_path + event_name + '_analyst.log')
    if output.exists():
        os.remove(output)

    catalogue_name = case.get('catalogue_name')

    for band in case.get('catalogue_bands'):
        output = Path(f'./{analyst_path}/{event_name}_CMD_{catalogue_name}_{band}.html')
        if output.exists():
            os.remove(output)

