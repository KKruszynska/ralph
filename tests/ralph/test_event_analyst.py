from ralph.analyst.event_analyst import EventAnalyst

scenario_file_cat = {
    'event_name' : 'GaiaDR3-ULENS-025',
    'ra' : 260.8781,
    'dec' : -27.3788,
    'analyst_path' : 'tests/ralph/data/output/event_analyst/',
    'config_final' : {
        'event_name': 'GaiaDR3-ULENS-025',
        'ra': 260.8781,
        'dec': -27.3788,
        'lc_analyst': {
            'n_max': 10,
             },
        'fit_analyst': {
            'fitting_package': 'pylima',
            'ongoing_magnification_thershold': 1.10,
            'ongoing_amplitude_thershold': 1.0,
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
    }
}

scenario_gsa = {
        'event_name': 'Gaia24amo',
        'ra': 249.14892083,
        'dec': -53.74991944,
        'analyst_path': 'tests/ralph/data/output/event_analyst/',
        'lc_analyst': {
            'n_max': 10,
        },
        'fit_analyst': {
            'fitting_package': 'pylima',
            'ongoing_magnification_thershold': 1.10,
            'ongoing_amplitude_thershold': 1.0,
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
        }

scenario_kwu = {
        'event_name': 'AT2024kwu',
        'ra': 102.93358333,
        'dec': 44.352166666,
        'analyst_path': 'tests/ralph/data/output/event_analyst/',
        'lc_analyst': {
            'n_max': 10,
        },
        'fit_analyst': {
            'fitting_package': 'pylima',
            'ongoing_magnification_thershold': 1.10,
            'ongoing_amplitude_thershold': 1.0,
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
        ]
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

    def test_run_analyst(self):
        """
        Test running a single event analyst.
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
    test.test_parse_config()

    case = scenario_gsa
    test = EventAnalystTest(case)
    test.test_run_analyst()

    case = scenario_kwu
    test = EventAnalystTest(case)
    test.test_run_analyst()
