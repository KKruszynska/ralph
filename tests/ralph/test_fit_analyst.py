import pytest

import json
from collections import OrderedDict

import numpy as np

from ralph.analyst.fit_analyst import FitAnalyst
from ralph.toolbox import logs, input_tools

scenario_gaia = {
        'analyst_path': 'tests/ralph/data/output/fit_analyst/',
        'event_name': 'GDR3-ULENS-025',
        'ra': 260.8781,
        'dec': -27.3788,
        'fit_analyst': {
            'fitting_package': 'pyLIMA'
        },
        'light_curves' : [
            {
                'survey': 'Gaia',
                'band': 'G',
                'ephemeris': 'tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt',
                'path' : 'tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_mod_G.dat',
           },
            {
                'survey': 'Gaia',
                'band': 'BP',
                'ephemeris': 'tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt',
                'path' : 'tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_mod_BP.dat',
                },
            {
                'survey': 'Gaia',
                'band': 'RP',
                'ephemeris': 'tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt',
                'path' : 'tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_mod_RP.dat',
            },
            {
                'survey': 'OGLE',
                'band': 'I',
                'path' : 'tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_mod_G.dat',
            },
        ],
        'fit_result' : 'tests/ralph/data/input/test_results/gdr3_ulens_025_fit_results.json'
}

scenario_gsa = {
        'event_name': 'Gaia24amo',
        'ra': 249.14892083,
        'dec': -53.74991944,
        'analyst_path': 'tests/ralph/data/output/fit_analyst/',
        'lc_analyst': {
            'n_max': 10,
        },
        'fit_analyst': {
            'fitting_package': 'pyLIMA'
        },
        'light_curves' : [
            {
                'survey': 'GSA',
                'band': 'G',
                'ephemeris': 'tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt',
                'path' : 'tests/ralph/data/input/light_curves/Gaia24amo_Gaia_G.dat',
            },
            {
                'survey': 'LCO',
                'band': 'g',
                'path' : 'tests/ralph/data/input/light_curves/Gaia24amo_LCO_g.dat',
            },
            {
                'survey': 'LCO',
                'band': 'r',
                'path' : 'tests/ralph/data/input/light_curves/Gaia24amo_LCO_r.dat',
                },
            {
                'survey': 'LCO',
                'band': 'i',
                'path' : 'tests/ralph/data/input/light_curves/Gaia24amo_LCO_i.dat',
            },
        ],
        }


class FitAnalystTest:
    """
    Class with tests
    """
    def __init__(self,
                 scenario):
        self.scenario = scenario

    def test_parse_config(self):
        """
        Test if parsing configuration file works.
        """

        config = {}
        config['event_name'] = self.scenario.get('event_name')
        path_outputs = self.scenario.get('analyst_path')
        config['ra'], config['dec'] = self.scenario.get('ra'), self.scenario.get('dec')
        config['fit_analyst'] = {}
        dict = self.scenario.get('fit_analyst')
        config['fit_analyst']['fitting_package'] = dict.get('fitting_package')
        config['light_curves'] = self.scenario.get('light_curves')

        light_curves = []
        for entry in config['light_curves']:
            survey = entry['survey']
            band = entry['band']
            data = input_tools.load_light_curve_from_path(entry['path'])

            if  any(s in entry['survey'] for s in ['Gaia', 'GSA']):
                ephemeris = input_tools.load_ephemeris_from_path(
                    entry['ephemeris'],
                    usecols = (0,1,2,3),
                )

                data[:, 0] = data[:, 0] + 2450000.0

                light_curves.append({
                    'light_curve': data,
                    'ephemeris': ephemeris,
                    'survey': survey,
                    'band': band,
                })
            else:
                light_curves.append({
                    'light_curve': data,
                    'survey': survey,
                    'band': band,
                })

        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'], stream=True)
        analyst = FitAnalyst(config['event_name'], path_outputs, light_curves, log, config_dict=config)
        f_pack_config = analyst.config['fit_analyst']['fitting_package']
        logs.close_log(log)

        assert f_pack_config == dict.get('fitting_package')

    def test_check_ongoing(self):
        """
        Check if testing for an ongoing event works.
        """

        config = {}
        config['event_name'] = self.scenario.get('event_name')
        path_outputs = self.scenario.get('analyst_path')
        config['ra'], config['dec'] = self.scenario.get('ra'), self.scenario.get('dec')
        config['fit_analyst'] = {}
        dict = self.scenario.get('fit_analyst')
        config['fit_analyst']['fitting_package'] = dict.get('fitting_package')
        config['light_curves'] = self.scenario.get('light_curves')

        light_curves = []
        for entry in config['light_curves']:
            survey = entry['survey']
            band = entry['band']
            data = input_tools.load_light_curve_from_path(entry['path'])

            if any(s in entry['survey'] for s in ['Gaia', 'GSA']):
                ephemeris = input_tools.load_ephemeris_from_path(
                    entry['ephemeris'],
                    usecols=(0, 1, 2, 3),
                )

                data[:, 0] = data[:, 0] + 2450000.0

                light_curves.append({
                    'light_curve': data,
                    'ephemeris': ephemeris,
                    'survey': survey,
                    'band': band,
                }
                )
            else:
                light_curves.append({
                    'light_curve': data,
                    'survey': survey,
                    'band': band,
                }
                )

        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'], stream=False)
        analyst = FitAnalyst(config['event_name'], path_outputs, light_curves, log, config_dict=config)
        status, t0 = analyst.perform_ongoing_check()
        logs.close_log(log)

        assert status == True

    def test_fit(self):
        """
        Test if fitting works.
        """

        config = {}
        config['event_name'] = self.scenario.get('event_name')
        path_outputs = self.scenario.get('analyst_path')
        config['ra'], config['dec'] = self.scenario.get('ra'), self.scenario.get('dec')
        config['fit_analyst'] = {}
        dict = self.scenario.get('fit_analyst')
        config['fit_analyst']['fitting_package'] = dict.get('fitting_package')
        config['light_curves'] = self.scenario.get('light_curves')

        light_curves = []
        for entry in config['light_curves']:
            survey = entry['survey']
            band = entry['band']
            data = input_tools.load_light_curve_from_path(entry['path'])

            if any(s in entry['survey'] for s in ['Gaia', 'GSA']):
                ephemeris = input_tools.load_ephemeris_from_path(
                    entry['ephemeris'],
                    usecols=(0, 1, 2, 3),
                )

                data[:, 0] = data[:, 0] + 2450000.0

                light_curves.append({
                    'light_curve': data,
                    'ephemeris': ephemeris,
                    'survey': survey,
                    'band': band,
                }
                )
            else:
                light_curves.append({
                    'light_curve': data,
                    'survey': survey,
                    'band': band,
                }
                )

        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'], stream=False)
        analyst = FitAnalyst(config['event_name'], path_outputs, light_curves, log, config_dict=config)
        result = analyst.perform_fit()

        with open(self.scenario.get('fit_result'), 'r') as file:
            expected_fit_result = json.load(file)

        for model in expected_fit_result:
            model_result = result[model]
            expected_result = expected_fit_result[model]
            assert pytest.approx(model_result['t0'], 2) == pytest.approx(expected_result['t0'], 2)

        logs.close_log(log)




def test_run():
    case = scenario_gaia
    test = FitAnalystTest(case)
    # test.test_parse_config()
    # test.test_check_ongoing()
    test.test_fit()
