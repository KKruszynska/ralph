import numpy as np

from ralph.analyst.light_curve_analyst import LightCurveAnalyst
from ralph.toolbox import input_tools, logs

scenario_gaia = {
        'path_outputs': 'tests/ralph/data/output/lc_analyst/',
        'event_name': 'GDR3-ULENS-025',
        'ra': 260.8781,
        'dec': -27.3788,
        'lc_analyst': {
            'acceptable_mag_range': {'upper_limit': -10,
                                     'lower_limit': 30}
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
                    'path' : 'tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_OGLE.dat',
                },
        ]
}

# scenario_gsa = {
#         'path_outputs': 'tests/ralph/data/output/lc_analyst/',
#         'event_name': 'Gaia24amo',
#         'ra': 249.14892083,
#         'dec': -53.74991944,
#         'fit_analyst': {
#             'fitting_package': 'pylima'
#         },
#         'lc_analyst': {
#             'n_max': 5
#         },
#         'light_curves' : [
#             {
#             'survey': 'GSA',
#             'band': 'G',
#             'lc' : needs to be fixed
#             },
#             {
#                 'survey': 'LCO',
#                 'band': 'i',
#                 'lc': needs to be fixed
#                 },
#             {
#             'survey': 'LCO',
#             'band': 'g',
#             'lc': needs to be fixed
#             },
#         ],
#         }

class LightCurveAnalystTest:
    """
    Class to test LightCurveAnalyst.

    :param scenario: a scenario to test with the LightCurveAnalyst.

    """
    def __init__(self,
                 scenario):
        self.scenario = scenario

    def test_parse_config(self):
        """
        Parse the configuration file and check if it is done as expected.
        """

        config = {}
        config['event_name'] = self.scenario.get('event_name')
        path_outputs = self.scenario.get('path_outputs')
        config['ra'], config['dec'] = self.scenario.get('ra'), self.scenario.get('dec')
        config['lc_analyst'] = {}
        dictionary = self.scenario.get('lc_analyst')
        config['lc_analyst']['acceptable_mag_range'] = dictionary.get('acceptable_mag_range')
        config['light_curves'] = self.scenario.get('light_curves')

        light_curves = []
        for entry in config['light_curves']:
            survey = entry['survey']
            band = entry['band']

            light_curve = input_tools.load_light_curve_from_path(entry['path'])

            light_curves.append({
                'event_name': config['event_name'],
                'lc': light_curve,
                'survey': survey,
                'band': band,
            })

        log = logs.start_log(path_outputs, 'debug',
                             event_name=config['event_name'], stream=True
                             )
        analyst = LightCurveAnalyst(config['event_name'], path_outputs,
                                    light_curves, log, config_dict=config
                                    )
        upper_mag = analyst.config['lc_analyst']['acceptable_mag_range']['upper_limit']
        lower_mag = analyst.config['lc_analyst']['acceptable_mag_range']['lower_limit']
        mag_range_dict = analyst.acceptable_mag_range
        logs.close_log(log)

        assert upper_mag == dictionary['acceptable_mag_range'].get('upper_limit')
        assert lower_mag == dictionary['acceptable_mag_range'].get('lower_limit')
        assert mag_range_dict == dictionary['acceptable_mag_range']

    def test_run_analyst(self):
        """
        Test running the Light Curve Analyst.
        """

        config = {}
        config['event_name'] = self.scenario.get('event_name')
        path_outputs = self.scenario.get('path_outputs')
        config['ra'], config['dec'] = self.scenario.get('ra'), self.scenario.get('dec')
        config['lc_analyst'] = {}
        dict = self.scenario.get('lc_analyst')
        config['lc_analyst']['n_max'] = dict.get('n_max')
        config['light_curves'] = self.scenario.get('light_curves')

        light_curves = []
        for entry in config['light_curves']:
            survey = entry['survey']
            band = entry['band']
            if ('path' in entry):
                light_curve = input_tools.load_light_curve_from_path(entry['path'])
                light_curves.append({
                    'lc': light_curve,
                    'survey': survey,
                    'band': band
                })

        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'])
        analyst = LightCurveAnalyst(config['event_name'], path_outputs, light_curves, log, config_dict=config)
        analyst.perform_quality_check()
        logs.close_log(log)

        for entry in analyst.light_curves:
            light_curve = entry['lc']
            negative_errs = np.where(light_curve[:, 2] < 0)
            assert len(negative_errs[0]) == len([])


class BadLightCurvesTest:
    """
    Class to test if bad quality light curves are correctly processed.
    """

    def test_bad_lc(self):
        """
        Test if bad light curves are handled correctly.
        """

        config = {}
        config['event_name'] = 'test_negative_errs'
        path_outputs = 'tests/ralph/data/output/lc_analyst/'
        config['ra'], config['dec'] = 1., 1.
        config['lc_analyst'] = {}
        config['lc_analyst']['n_max'] = 10.

        dict = {
                'survey': 'GSA',
                'band': 'G',
                'lc': [[2457000., 17.00, -0.02], [2457001., 17.01, np.nan], [2457002., 17.02, 0.02],
                       [2457003., np.inf, 0.02], [2457004., 17.04, -0.02], [2457005., 17.05, 0.02],
                       [2457006., np.nan, 0.02], [2457007., 17.09, 0.02], [2457008., 17.2, 0.02],
                       [2457006., 17.0, np.inf], [2457007., 17.09, 0.02], [2457008., 17.2, 0.02], ],
                }

        light_curves = [dict]
        config['light_curves'] = light_curves

        log = logs.start_log(path_outputs, 'debug', event_name=config['event_name'], stream=True)
        analyst = LightCurveAnalyst(config['event_name'], path_outputs, light_curves, log, config_dict=config)
        analyst.perform_quality_check()

        for entry in analyst.light_curves:
            lc = entry['lc']

            negative_errs = np.where(lc[:, 2] < 0)
            assert len(negative_errs[0]) == len([])

            out_of_bounds = np.where(lc[:, 1] < -10)
            assert len(out_of_bounds[0]) == len([])
            out_of_bounds = np.where(lc[:, 1] > 40)
            assert len(out_of_bounds[0]) == len([])

            unique_entries = np.unique(lc[:, 0])
            assert len(unique_entries) == len(lc[:, 0])

            finite_mag = np.isfinite(lc[:, 1])
            finite_err = np.isfinite(lc[:, 2])

            assert len(finite_mag) == len(lc[:, 0])
            assert len(finite_err) == len(lc[:, 0])

        logs.close_log(log)


def test_run():
    """
    Run all tests.
    """

    case = scenario_gaia
    test = LightCurveAnalystTest(case)
    test.test_parse_config()
    test.test_run_analyst()

    # case = scenario_gsa
    # test = TestLCAnalyst(case)
    # test.test_run_analyst()

    test = BadLightCurvesTest()
    test.test_bad_lc()
