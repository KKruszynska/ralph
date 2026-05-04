import pytest
import json
import numpy as np
from pathlib import Path

import os

from ralph.controller.controller import Controller

# class TestControllerDicts:
#     """
#     Tests to check if controller works fine.
#     """
#
#     def test_launch_analysts(self):
#         from MFPipeline.controller.controller import Controller
#
#
#
#         event_list = ['GaiaDR3-ULENS-018',
#                       'GaiaDR3_ULENS_025',
#                       ]
#
#         event_info = pd.read_csv('tests/test_controller/events_info.csv', header=0)
#
#         analyst_jsons = {}
#         path_lightcurves = 'tests/test_controller/light_curves/'
#         os.chdir(path_lightcurves)
#         for event in event_list:
#             dictionary = {}
#             idx = event_info.index[event_info['#event_name'] == event].tolist()
#             dictionary['event_name'] = event
#             dictionary['ra'], '%f'%event_info['ra'].values[idx][0]
#             dictionary['dec'] = '%f'%event_info['dec'].values[idx][0]
#             dictionary['lc_analyst'] = {}
#             dictionary['lc_analyst']['n_max'] = '%d'%event_info['lc_nmax'].values[idx][0]
#             dictionary['fit_analyst'] = {}
#             dictionary['fit_analyst']['fitting_package'] = 'pylima'
#
#             # cats = event_info['catalogues'].values[idx][0].split(' ')
#             # cat_list = []
#             # for catalogue in cats:
#             #     dict = {}
#             #     dict['name'] = catalogue
#             #     dict['bands'] = event_info['bands'].values[idx][0].split(' ')
#             #     if (len(event_info['path'].values[idx]) > 0):
#             #         dict['cmd_path'] = event_info['path'].values[idx][0]
#             #         dict['cmd_separator'] = ','
#             #     cat_list.append(dict)
#             # dictionary['cmd_analyst'] = {}
#             # dictionary['cmd_analyst']['catalogues'] = cat_list
#
#             light_curves = []
#             for file in glob.glob('*%s*.dat' % event):
#                 light_curve = np.genfromtxt(file, usecols=(0, 1, 2), unpack=True)
#                 light_curve = light_curve.T
#
#                 survey = ''
#                 band = ''
#                 if ('mod' in file):
#                     survey = 'Gaia'
#                     txt = file.split('.')
#                     band = txt[0].split('_')[-1]
#                     light_curve[:, 0] = light_curve[:, 0] + 2450000.
#                 elif ('OGLE' in file):
#                     survey = 'OGLE'
#                     band = 'I'
#                 elif ('KMT' in file):
#                     survey = 'KMTNet_' + file[-7]
#                     band = 'I'
#
#                 dict = {
#                     'survey': survey,
#                     'band': band,
#                     'lc': json.dumps(light_curve.tolist())
#                 }
#                 light_curves.append(dict)
#
#             dictionary['light_curves'] = light_curves
#             js = json.dumps(dictionary)
#             analyst_jsons[event] = js
#
#         os.chdir('../../../')
#         config = {
#             'python_compiler': 'python',
#             'group_processing_limit': 3,
#             'events_path': 'tests/test_controller/',
#             'software_dir': 'MFPipeline/analyst/',
#             'log_stream': False,
#             'log_location':
#                 'tests/test_controller/',
#             'log_level': 'debug'
#             }
#
#         controller = Controller(event_list, config_dict=config, analyst_dicts=analyst_jsons)
#         controller.launch_analysts()


# class TestControllerOngoing:
#     """
#     Tests to check if controller works fine.
#     """
#
#     def test_launch_analysts(self):
#         from MFPipeline.controller.controller import Controller
#
#         # event_list = ['Gaia24amo', 'Gaia24cbz', 'AT2024kwu', 'GaiaDR3-ULENS-018',
#         #               'GaiaDR3_ULENS_025']
#
#         # event_list = ['Gaia24amo', 'AT2024kwu', 'GaiaDR3-ULENS-018']
#         event_list = ['Gaia24amo']
#
#         coordinates = {
#             'Gaia24amo': {
#                 'ra': 249.14892083,
#                 'dec': -53.74991944,
#             },
#             'Gaia24cbz': {
#                 'ra': 251.87178,
#                 'dec': -47.20051,
#             },
#             'AT2024kwu': {
#                 'ra': 102.93358333,
#                 'dec': 44.352166666,
#             },
#             'GaiaDR3-ULENS-018': {
#                 'ra': 271.119,
#                 'dec': -29.8162,
#             },
#             'GaiaDR3_ULENS_025': {
#                 'ra': 260.8781,
#                 'dec': -27.3788,
#             },
#         }
#
#         analyst_jsons = {}
#         path_lightcurves = './examples/light_curves/'
#         # path_lightcurves = '../examples/light_curves/'
#         os.chdir(path_lightcurves)
#
#         for event in event_list:
#             dictionary = {
#                 'event_name': event,
#                 'ra': '%f' % coordinates[event]['ra'],
#                 'dec': '%f' % coordinates[event]['dec'],
#                 'lc_analyst': {
#                     'n_max': 10,
#                 },
#             'fit_analyst': {
#                 'fitting_package': 'pylima',
#                 }
#             }
#
#             light_curves = []
#             for file in glob.glob('*%s*.dat' % event):
#                 light_curve = np.genfromtxt(file, usecols=(0, 1, 2), unpack=True)
#                 light_curve = light_curve.T
#
#                 survey = ''
#                 band = ''
#
#                 if 'GSA' in file:
#                     survey = 'Gaia'
#                     txt = file.split('.')
#                     band = txt[0].split('_')[-1]
#                 elif 'LCO' in file:
#                     survey = 'LCO'
#                     txt = file.split('.')
#                     band = txt[0].split('_')[-1]
#                 elif 'ZTF' in file:
#                     survey = 'ZTF'
#                     txt = file.split('.')
#                     band = txt[0].split('_')[-1]
#                 elif 'ATLAS' in file:
#                     survey = 'ATLAS'
#                     txt = file.split('.')
#                     band = txt[0].split('_')[-1]
#                 elif ('mod' in file):
#                     survey = 'Gaia'
#                     txt = file.split('.')
#                     band = txt[0].split('_')[-1]
#                     light_curve[:, 0] = light_curve[:, 0] + 2450000.
#                 elif ('OGLE' in file):
#                     survey = 'OGLE'
#                     band = 'I'
#                 elif ('KMT' in file):
#                     survey = 'KMTNet_' + file[-7]
#                     band = 'I'
#                     light_curve[:, 0] = light_curve[:, 0] + 2450000.
#
#                 lc_dict = {
#                     'survey': survey,
#                     'band': band,
#                     'lc': json.dumps(light_curve.tolist())
#                 }
#                 light_curves.append(lc_dict)
#
#             dictionary['light_curves'] = light_curves
#             file_name = '../../tests/test_controller_ongoing/' + '%s.json' % (event)
#             with open(file_name, 'w', encoding='utf-8') as file:
#                 json.dump(dictionary, file, ensure_ascii=False, indent=4)
#             js = json.dumps(dictionary)
#             analyst_jsons[event] = js
#
#
#         path_lightcurves = '../../'
#         os.chdir(path_lightcurves)
#
#         config = {
#             'python_compiler': 'python',
#             'group_processing_limit': 1,
#             'events_path':
#                 'tests/test_controller_ongoing/',
#             'software_dir':
#                 'MFPipeline/analyst/',
#             'log_stream': False,
#             'log_location':
#                 'tests/test_controller_ongoing/',
#             'log_level': 'debug'
#         }
#
#         controller = Controller(event_list, config_dict=config, analyst_dicts=analyst_jsons)
#         controller.launch_analysts()

class ControllerPathsTest:
    """
    Tests to check if controller works for a finished event.
    """

    def __init__(self,
                 expected_results):
        self.expected_results = expected_results

    def test_launch_analysts(self):
        """
        Run controller to check if it works.
        """
        event_list = [
                      'GaiaDR3_ULENS_025',
                      ]

        config = {
            'python_compiler': 'python',
            'group_processing_limit': 1,
            'events_path':
                'tests/ralph/data/input/controller/',
            'software_dir':
                'src/ralph/analyst/',
            'config_type': 'yaml',
            'log_stream': False,
            'log_location':
                'tests/ralph/data/output/controller_launch/',
            'log_level': 'debug'
            }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()

        # Check if expected files exist
        # Controller log
        controller_log_path = 'tests/ralph/data/output/controller_launch/'
        output = Path(controller_log_path + 'controller.log')
        assert output.exists() is True
        assert output.is_file() is True

        # Analyst output files
        analyst_home = 'tests/ralph/data/input/controller/'
        for event in event_list:
            analyst_path = analyst_home + event

            output = Path(analyst_path)
            assert output.exists() is True
            assert output.is_dir() is True

            output = Path(analyst_path + '/fit_results.json')
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + '/fit_stats.txt')
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + '/' + event + '_analyst.log')
            assert output.exists() is True
            assert output.is_file() is True

            model_plots = [
                'PSPL_no_blend_no_piE',
                'PSPL_blend_no_piE',
                'PSPL_blend_piE',
            ]

            for file_path in model_plots:
                output = Path(analyst_path + '/' + file_path + '.html')
                assert output.exists() is True
                assert output.is_file() is True

            bands = [
                '_CMD_Gaia_DR3_Gaia_G',
                '_CMD_Gaia_DR3_Gaia_BP',
                '_CMD_Gaia_DR3_Gaia_RP',
            ]
            for model in model_plots:
                for band in bands:
                    output = Path(analyst_path + '/' + event + '_' + model + band + '.html')
                    assert output.exists() is True
                    assert output.is_file() is True

            expected_result_path = self.expected_results[event]
            with open(expected_result_path, 'r') as file:
                expected_fit_result = json.load(file)

            with open(analyst_path + '/fit_results.json', 'r') as file:
                received_fit_result = json.load(file)

            for model in expected_fit_result:
                model_result = received_fit_result[model]
                expected_result = expected_fit_result[model]
                for key in expected_result:
                    expected = float(expected_result[key])
                    received = float(model_result[key])
                    if not np.isnan(expected):
                        assert pytest.approx(received, 2) == pytest.approx(expected, 2)


class ControllerPathsOngoingTest:
    """
    Tests to check if controller works fine for ongoing events.
    """
    def __init__(self,
                 expected_results):
        self.expected_results = expected_results

    def test_launch_analysts(self):
        """
        Run controller to check if it works.
        """

        # event_list = ['Gaia24amo', 'Gaia24cbz', 'AT2024kwu', 'GaiaDR3_ULENS_018',
        #               'GaiaDR3_ULENS_025']

        event_list = [
            'AT2024kwu',
            'GaiaDR3_ULENS_018'
        ]

        config = {
            'python_compiler': 'python',
            'group_processing_limit': 1,
            'config_type': 'yaml',
            'events_path':
                'tests/ralph/data/input/controller/',
            'software_dir':
                'src/ralph/analyst/',
            'log_stream': False,
            'log_location':
                'tests/ralph/data/output/controller_analysts/',
            'log_level': 'debug'
        }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()

        # Check if expected files exist
        # Controller log
        controller_log_path = 'tests/ralph/data/output/controller_analysts/'
        output = Path(controller_log_path + 'controller.log')
        assert output.exists() is True
        assert output.is_file() is True

        # Analyst output files
        analyst_home = 'tests/ralph/data/input/controller/'
        for event in event_list:
            analyst_path = analyst_home + event

            output = Path(analyst_path)
            assert output.exists() is True
            assert output.is_dir() is True

            output = Path(analyst_path + '/fit_results.json')
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + '/fit_stats.txt')
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + '/' + event + '_analyst.log')
            assert output.exists() is True
            assert output.is_file() is True

            model_plots = [
                'PSPL_no_blend_no_piE',
                'PSPL_blend_no_piE',
                'PSPL_blend_piE',
            ]

            for file_path in model_plots:
                output = Path(analyst_path + '/' + file_path + '.html')
                assert output.exists() is True
                assert output.is_file() is True

            expected_result_path = self.expected_results[event]
            with open(expected_result_path, 'r') as file:
                expected_fit_result = json.load(file)

            with open(analyst_path + '/fit_results.json', 'r') as file:
                received_fit_result = json.load(file)

            for model in expected_fit_result:
                model_result = received_fit_result[model]
                expected_result = expected_fit_result[model]
                for key in expected_result:
                    expected = float(expected_result[key])
                    received = float(model_result[key])
                    if not np.isnan(expected):
                        assert pytest.approx(received, 2) == pytest.approx(expected, 2)

def test_run():
    """
    Run all tests.
    """

    expected_fit_results = {
        'GaiaDR3_ULENS_025' : 'tests/ralph/data/input/test_results/gdr3_ulens_025_fit_results.json',
        'AT2024kwu' : 'tests/ralph/data/input/test_results/at2024kwu_fit_results.json',
        'GaiaDR3_ULENS_018' : 'tests/ralph/data/input/test_results/gdr3_ulens_018_fit_results.json',
    }

    test = ControllerPathsTest(expected_fit_results)
    test.test_launch_analysts()

    test = ControllerPathsOngoingTest(expected_fit_results)
    test.test_launch_analysts()

    controller_log_path = [
        'tests/ralph/data/output/controller_launch/',
        'tests/ralph/data/output/controller_analysts/',
    ]
    for controller_path in controller_log_path:
        output = Path(controller_path + 'controller.log')
        if output.exists():
            os.remove(output)
    analyst_home = 'tests/ralph/data/input/controller/'
    for event in expected_fit_results:
        analyst_path = analyst_home + event

        output = Path(analyst_path + '/fit_results.json')
        if output.exists():
            os.remove(output)

        output = Path(analyst_path + '/fit_stats.txt')
        if output.exists():
            os.remove(output)

        output = Path(analyst_path + '/' + event + '_analyst.log')
        if output.exists():
            os.remove(output)

        model_plots = [
            'PSPL_no_blend_no_piE',
            'PSPL_blend_no_piE',
            'PSPL_blend_piE',
        ]

        for file_path in model_plots:
            output = Path(analyst_path + '/' + file_path + '.html')
            if output.exists():
                os.remove(output)

        bands = [
            '_CMD_Gaia_DR3_Gaia_G',
            '_CMD_Gaia_DR3_Gaia_BP',
            '_CMD_Gaia_DR3_Gaia_RP',
        ]
        for model in model_plots:
            for band in bands:
                output = Path(analyst_path + '/' + event + '_' + model + band + '.html')
                if output.exists():
                    os.remove(output)
