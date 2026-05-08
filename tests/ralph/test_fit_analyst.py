import json
import os
from pathlib import Path

import numpy as np
import pytest

from ralph.analyst.fit_analyst import FitAnalyst
from ralph.toolbox import input_tools, logs

scenario_gaia = {
    "analyst_path": "tests/ralph/data/output/fit_analyst/",
    "event_name": "GaiaDR3_ULENS_025",
    "ra": 260.8781,
    "dec": -27.3788,
    "fit_analyst": {
        "ongoing_magnification_thershold": 1.10,
        "ongoing_amplitude_thershold": 1.0,
        "model_fit_configuration": {
            "PSPL_no_blend_no_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "DE",
                "boundaries": {
                    "u0": [0.0, 2.0],
                }
            },
            "PSPL_blend_no_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "TRF",
                "boundaries": {
                    "u0": [0.0, 2.0],
                }
            },
            "PSPL_blend_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "TRF",
                "boundaries": {
                    "u0": [0.0, 2.0],
                    "piEN": [-1.0, 1.0],
                    "piEE": [-1.0, 1.0],
                }
            },
            "PSPL_no_blend_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "TRF",
                "boundaries": {
                    "u0": [0.0, 2.0],
                    "piEN": [-1.0, 1.0],
                    "piEE": [-1.0, 1.0],
                }
            },
        }
    },
    "light_curves": [
        {
            "survey": "Gaia",
            "band": "G",
            "ephemeris": "tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt",
            "path": "tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_Gaia_G.dat",
        },
        {
            "survey": "Gaia",
            "band": "BP",
            "ephemeris": "tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt",
            "path": "tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_Gaia_BP.dat",
        },
        {
            "survey": "Gaia",
            "band": "RP",
            "ephemeris": "tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt",
            "path": "tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_Gaia_RP.dat",
        },
        {
            "survey": "OGLE",
            "band": "I",
            "path": "tests/ralph/data/input/light_curves/GaiaDR3_ULENS_025_OGLE.dat",
        },
    ],
    "fit_result": "tests/ralph/data/input/test_results/gdr3_ulens_025_fit_results.json",
}

scenario_gsa = {
    "event_name": "Gaia24amo",
    "ra": 249.14892083,
    "dec": -53.74991944,
    "analyst_path": "tests/ralph/data/output/fit_analyst/",
    "lc_analyst": {
        "n_max": 10,
    },
    "fit_analyst": {
        "ongoing_magnification_thershold": 1.10,
        "ongoing_amplitude_thershold": 1.0,
        "model_fit_configuration": {
            "PSPL_no_blend_no_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "DE",
                "boundaries": {
                    "u0": [0.0, 2.0],
                }
            },
            "PSPL_blend_no_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "TRF",
                "boundaries": {
                    "u0": [0.0, 2.0],
                }
            },
            "PSPL_blend_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "TRF",
                "boundaries": {
                    "u0": [0.0, 2.0],
                    "piEN": [-1.0, 1.0],
                    "piEE": [-1.0, 1.0],
                }
            },
            "PSPL_no_blend_piE": {
                "fitting_package": "pyLIMA",
                "fitting_method": "TRF",
                "boundaries": {
                    "u0": [0.0, 2.0],
                    "piEN": [-1.0, 1.0],
                    "piEE": [-1.0, 1.0],
                }
            },
        }
    },
    "light_curves": [
        {
            "survey": "Gaia",
            "band": "G",
            "ephemeris": "tests/ralph/data/input/ephemeris/gaia_jpl_horizons_results.txt",
            "path": "tests/ralph/data/input/light_curves/Gaia24amo_GSA_G.dat",
        },
        {
            "survey": "LCO",
            "band": "g",
            "path": "tests/ralph/data/input/light_curves/cleaned_Gaia24amo_LCO_g.dat",
        },
        {
            "survey": "LCO",
            "band": "r",
            "path": "tests/ralph/data/input/light_curves/cleaned_Gaia24amo_LCO_r.dat",
        },
        {
            "survey": "LCO",
            "band": "i",
            "path": "tests/ralph/data/input/light_curves/cleaned_Gaia24amo_LCO_i.dat",
        },
    ],
}


class FitAnalystTest:
    """
    Class with tests
    """

    def __init__(self, scenario):
        self.scenario = scenario

    def test_parse_config(self):
        """
        Test if parsing configuration file works.
        """

        config = {
            "event_name": self.scenario.get("event_name"),
            "ra": self.scenario.get("ra"),
            "dec": self.scenario.get("dec"),
            }

        fit_params = self.scenario.get("fit_analyst")

        config["fit_analyst"] = {
            "ongoing_magnification_thershold": fit_params.get("ongoing_magnification_thershold"),
            "ongoing_amplitude_thershold": fit_params.get("ongoing_amplitude_thershold"),
        }

        model_params = fit_params.get("model_fit_configuration")
        params = {}
        for model in model_params:
            params[model] = model_params.get(model)
        config["fit_analyst"]["model_fit_configuration"] = params

        config["light_curves"] = self.scenario.get("light_curves")


        path_outputs = self.scenario.get("analyst_path")

        light_curves = []
        for entry in config["light_curves"]:
            survey = entry["survey"]
            band = entry["band"]
            data = input_tools.load_light_curve_from_path(entry["path"])

            ephemeris = None
            if entry == "ephemeris":
                ephemeris = input_tools.load_ephemeris_from_path(
                    entry["ephemeris"],
                    usecols=(0, 1, 2, 3),
                )

            light_curves.append(
                {
                    "light_curve": data,
                    "ephemeris": ephemeris,
                    "survey": survey,
                    "band": band,
                }
            )


        log = logs.start_log(path_outputs, "debug", event_name=config["event_name"], stream=True)
        analyst = FitAnalyst(config["event_name"], path_outputs, light_curves, log, config_dict=config)
        on_mag_t_config = analyst.config["fit_analyst"]["ongoing_magnification_thershold"]
        on_ampl_t_config = analyst.config["fit_analyst"]["ongoing_amplitude_thershold"]
        model_fit_config = analyst.config["fit_analyst"]["model_fit_configuration"]

        logs.close_log(log)

        assert on_mag_t_config == fit_params.get("ongoing_magnification_thershold")
        assert on_ampl_t_config == fit_params.get("ongoing_amplitude_thershold")

        model_params = fit_params.get("model_fit_configuration")
        for model in model_fit_config:
            params = model_fit_config[model]
            for key in params:
                assert model_params[model][key] == params.get(key)

    def test_check_ongoing(self):
        """
        Check if testing for an ongoing event works.
        """

        config = {
            "event_name": self.scenario.get("event_name"),
            "ra": self.scenario.get("ra"),
            "dec": self.scenario.get("dec"),
            }

        fit_params = self.scenario.get("fit_analyst")

        config["fit_analyst"] = {
            "ongoing_magnification_thershold": fit_params.get("ongoing_magnification_thershold"),
            "ongoing_amplitude_thershold": fit_params.get("ongoing_amplitude_thershold"),
        }

        model_params = fit_params.get("model_fit_configuration")
        params = {}
        for model in model_params:
            params[model] = model_params.get(model)
        config["fit_analyst"]["model_fit_configuration"] = params

        config["light_curves"] = self.scenario.get("light_curves")


        path_outputs = self.scenario.get("analyst_path")

        light_curves = []
        for entry in config["light_curves"]:
            survey = entry["survey"]
            band = entry["band"]
            data = input_tools.load_light_curve_from_path(entry["path"])

            ephemeris = None
            if entry == "ephemeris":
                ephemeris = input_tools.load_ephemeris_from_path(
                    entry["ephemeris"],
                    usecols=(0, 1, 2, 3),
                )

            light_curves.append(
                {
                    "light_curve": data,
                    "ephemeris": ephemeris,
                    "survey": survey,
                    "band": band,
                }
            )

        log = logs.start_log(path_outputs, "debug", event_name=config["event_name"], stream=False)
        analyst = FitAnalyst(config["event_name"], path_outputs, light_curves, log, config_dict=config)
        status, t0 = analyst.perform_ongoing_check()
        logs.close_log(log)

        assert status

    def test_fit(self):
        """
        Test if fitting works.
        """

        config = {
            "event_name": self.scenario.get("event_name"),
            "ra": self.scenario.get("ra"),
            "dec": self.scenario.get("dec"),
            }

        fit_params = self.scenario.get("fit_analyst")

        config["fit_analyst"] = {
            "ongoing_magnification_thershold": fit_params.get("ongoing_magnification_thershold"),
            "ongoing_amplitude_thershold": fit_params.get("ongoing_amplitude_thershold"),
        }

        model_params = fit_params.get("model_fit_configuration")
        params = {}
        for model in model_params:
            params[model] = model_params.get(model)
        config["fit_analyst"]["model_fit_configuration"] = params

        config["light_curves"] = self.scenario.get("light_curves")


        path_outputs = self.scenario.get("analyst_path")

        light_curves = []
        for entry in config["light_curves"]:
            survey = entry["survey"]
            band = entry["band"]
            data = input_tools.load_light_curve_from_path(entry["path"])

            ephemeris = None
            if entry == "ephemeris":
                ephemeris = input_tools.load_ephemeris_from_path(
                    entry["ephemeris"],
                    usecols=(0, 1, 2, 3),
                )

            light_curves.append(
                {
                    "light_curve": data,
                    "ephemeris": ephemeris,
                    "survey": survey,
                    "band": band,
                }
            )

        log = logs.start_log(path_outputs, "debug", event_name=config["event_name"], stream=False)
        analyst = FitAnalyst(config["event_name"], path_outputs, light_curves, log, config_dict=config)
        result = analyst.perform_fit()

        with open(self.scenario.get("fit_result"), "r") as file:
            expected_fit_result = json.load(file)

        for model in expected_fit_result:
            if model != "PSPL_no_blend_no_piE":
                model_result = result[model]
                expected_result = expected_fit_result[model]
                for key in expected_result:
                    expected = float(expected_result[key])
                    received = float(model_result[key])
                    if not np.isnan(expected):
                        assert pytest.approx(expected, 2) == pytest.approx(received, 2)

        logs.close_log(log)


def test_run():
    """
    Run all tests.
    """
    case = scenario_gaia
    test = FitAnalystTest(case)
    test.test_parse_config()
    test.test_check_ongoing()
    test.test_fit()

    for case in [scenario_gaia, scenario_gsa]:
        analyst_path = case.get("analyst_path")
        event_name = case.get("event_name")

        output = Path(analyst_path + "fit_results.json")
        if output.exists():
            os.remove(output)

        output = Path(analyst_path + "fit_stats.txt")
        if output.exists():
            os.remove(output)

        output = Path(analyst_path + event_name + "_analyst.log")
        print(output)
        if output.exists():
            os.remove(output)

        files = [
            "PSPL_no_blend_no_piE.html",
            "PSPL_blend_no_piE.html",
            "PSPL_blend_piE.html",
        ]
        for element in files:
            output = Path(analyst_path + element)
            if output.exists():
                os.remove(output)
