import pytest

from pathlib import Path
import json

from ralph.analyst.event_analyst import EventAnalyst

scenario_file_cat = {
    'event_name' : 'GaiaDR3_ULENS_025',
    'ra' : 260.8781,
    'dec' : -27.3788,
    'analyst_path' : 'tests/ralph/data/output/event_analyst/GDR3_ULENS_025/',
    'fit_result': 'tests/ralph/data/input/test_results/gdr3_ulens_025_fit_results.json',
    'config_final' : {
        'event_name': 'GaiaDR3_ULENS_025',
        'ra': 260.8781,
        'dec': -27.3788,
        'analyst_path' : 'tests/ralph/data/output/event_analyst/GDR3_ULENS_025/',
        'lc_analyst': {
            'n_max': 10,
            'ongoing_magnification_thershold': 1.05,
            'ongoing_amplitude_thershold': 1.0,
             },
        'fit_analyst': {
            'fitting_package': 'pylima',
        },
        'cmd_analyst':
            {'catalogues':
                 [{'name': 'Gaia_DR3',
                   'band': ['Gaia_G', 'Gaia_BP', 'Gaia_RP'],
                   'cmd_path':
                       'tests/ralph/data/input/cmd/gdr3_ulens_025_result.csv',
                   'cmd_separator': ','},
                ]
             },
    },
    'final_files': {
        'event_folder': 'GDR3_ULENS_025',
        'analyst_log': 'GaiaDR3_ULENS_025_analyst.log',
        'model_plots': [
            'PSPL_no_blend_no_piE.html',
            'PSPL_no_blend_no_piE.html',
            'PSPL_no_blend_no_piE.html',
        ],
        'cmd_plots:': [
            'GaiaDR3_ULENS_025_PSPL_blend_no_piE_CMD_Gaia_DR3_Gaia_BP.html',
            'GaiaDR3_ULENS_025_PSPL_blend_no_piE_CMD_Gaia_DR3_Gaia_RP.html',
            'GaiaDR3_ULENS_025_PSPL_blend_no_piE_CMD_Gaia_DR3_Gaia_G.html',
            'GaiaDR3_ULENS_025_PSPL_no_blend_no_piE_CMD_Gaia_DR3_Gaia_BP.html',
            'GaiaDR3_ULENS_025_PSPL_no_blend_no_piE_CMD_Gaia_DR3_Gaia_G.html',
            'GaiaDR3_ULENS_025_PSPL_no_blend_no_piE_CMD_Gaia_DR3_Gaia_RP.html',
            'GaiaDR3_ULENS_025_PSPL_blend_piE_CMD_Gaia_DR3_Gaia_BP.html',
            'GaiaDR3_ULENS_025_PSPL_blend_piE_CMD_Gaia_DR3_Gaia_G.html',
            'GaiaDR3_ULENS_025_PSPL_blend_piE_CMD_Gaia_DR3_Gaia_RP.html'
        ],
    },
}

scenario_gsa = {
        'event_name': 'Gaia24amo',
        'ra': 249.14892083,
        'dec': -53.74991944,
        'analyst_path': 'tests/ralph/data/output/event_analyst/Gaia24amo/',
        'fit_result': 'tests/ralph/data/input/test_results/gaia24amo_fit_results.json',
        'lc_analyst': {
            'n_max': 10,
            'ongoing_magnification_thershold': 1.10,
            'ongoing_amplitude_thershold': 1.0,
        },
        'fit_analyst': {
            'fitting_package': 'pylima',
        },
        'light_curves' : [
            {
                'survey': 'Gaia',
                'band': 'G',
                'ephemeris': 'tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt',
                'path' : 'tests/ralph/data/input/light_curves/Gaia24amo_Gaia_G.dat',
            },
            {
                'survey': 'LCO',
                'band': 'g',
                'path' : 'tests/ralph/data/input/light_curves/cleaned_Gaia24amo_LCO_g.dat',
            },
            {
                'survey': 'LCO',
                'band': 'r',
                'path' : 'tests/ralph/data/input/light_curves/cleaned_Gaia24amo_LCO_r.dat',
                },
            {
                'survey': 'LCO',
                'band': 'i',
                'path' : 'tests/ralph/data/input/light_curves/cleaned_Gaia24amo_LCO_i.dat',
            },
        ],
    'final_files': {
        'event_folder': 'Gaia24amo',
        'analyst_log': 'Gaia24amo_analyst.log',
        'model_plots': [
            'PSPL_no_blend_no_piE.html',
            'PSPL_no_blend_no_piE.html',
            'PSPL_no_blend_no_piE.html',
        ],
    },
}

scenario_kwu = {
        'event_name': 'AT2024kwu',
        'ra': 102.93358333,
        'dec': 44.352166666,
        'analyst_path': 'tests/ralph/data/output/event_analyst/AT2024kwu/',
        'fit_result': 'tests/ralph/data/input/test_results/at2024kwu_fit_results.json',
        'lc_analyst': {
            'n_max': 10,
            'ongoing_magnification_thershold': 1.10,
            'ongoing_amplitude_thershold': 1.0,
        },
        'fit_analyst': {
            'fitting_package': 'pylima',
        },
        'light_curves' : [
            {
                'survey': 'Gaia',
                'band': 'G',
                'ephemeris': 'tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt',
                'path' : 'tests/ralph/data/input/light_curves/AT2024kwu_Gaia_G.dat',
            },
            {
                'survey': 'LCO',
                'band': 'g',
                'path' : 'tests/ralph/data/input/light_curves/AT2024kwu_LCO_g.dat',
            },
            {
                'survey': 'LCO',
                'band': 'r',
                'path' : 'tests/ralph/data/input/light_curves/AT2024kwu_LCO_r.dat',
            },
            {
                'survey': 'LCO',
                 'band': 'i',
                 'path' : 'tests/ralph/data/input/light_curves/AT2024kwu_LCO_i.dat',
            },
            {
                'survey': 'ZTF',
                'band': 'g',
                'path' : 'tests/ralph/data/input/light_curves/AT2024kwu_ZTF_g.dat',
            },
            {
                'survey': 'ZTF',
                'band': 'r',
                'path' : 'tests/ralph/data/input/light_curves/AT2024kwu_ZTF_r.dat',
            },
        ],
    'final_files': {
        'event_folder': 'AT2024kwu',
        'analyst_log': 'AT2024kwu_analyst.log',
        'model_plots': [
            'PSPL_no_blend_no_piE.html',
            'PSPL_no_blend_no_piE.html',
            'PSPL_no_blend_no_piE.html',
        ],
    },
}

class EventAnalystTest:
    """
    Class with Event Analyst tests
    """
    def __init__(self,
                 scenario):
        self.scenario = scenario

    def test_parse_config(self):
        """
        Test if configuration is parsed correctly.
        """

        event_name = self.scenario.get('event_name')
        analyst_path = self.scenario.get('analyst_path')
        event_analyst = EventAnalyst(event_name, analyst_path,
                                     'debug',
                                     config_path=analyst_path+'config.yaml',
                                     stream=True
                                     )
        event_analyst.parse_config(analyst_path+'config.yaml')

        assert type(event_analyst.config) is type(self.scenario.get('config_final'))

        for element in event_analyst.config:
            assert event_analyst.config[element] == self.scenario.get('config_final')[element]

    def test_run_analyst_file(self):
        """
        Test running a single event analyst with config from a file.
        """

        event_name = self.scenario.get('event_name')
        analyst_path = self.scenario.get('analyst_path')
        event_analyst = EventAnalyst(event_name, analyst_path, 'debug', config_path=analyst_path+'config.yaml',
                                     stream=True)
        event_analyst.run_single_analyst()

        # Check if expected files exist
        #
        # if my_file.exists():
        # # path exists
        #
        # my_file = Path("/path/to/file")
        # if my_file.is_file():
        #
        #     if my_file.is_dir():
        # # directory exists


        with open(self.scenario.get('fit_result'), 'r') as file:
            expected_fit_result = json.load(file)

        for model in expected_fit_result:
            model_result = result[model]
            expected_result = expected_fit_result[model]
            assert pytest.approx(model_result['t0'], 2) == pytest.approx(expected_result['t0'], 2)

    def test_run_analyst_dict(self):
        """
        Test running a single event analyst with a config from a dictionary.
        """

        event_name = self.scenario.get('event_name')
        analyst_path = self.scenario.get('analyst_path')
        event_analyst = EventAnalyst(event_name, analyst_path, 'debug', config_dict=self.scenario,
                                     stream=False)
        event_analyst.run_single_analyst()


def test_run():
    """
    Run all tests.
    """

    case = scenario_file_cat
    test = EventAnalystTest(case)
    # test.test_parse_config()
    test.test_run_analyst_file()

    # case = scenario_gsa
    # test = EventAnalystTest(case)
    # test.test_run_analyst_dict()

    # case = scenario_kwu
    # test = EventAnalystTest(case)
    # test.test_run_analyst_dict()
