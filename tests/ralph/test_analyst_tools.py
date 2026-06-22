import pytest

from ralph.toolbox import input_tools
from ralph.analyst import analyst_tools

scenario_gaia = {
    "event_name": "GDR3_ULENS_025",
    "time_of_peak": 2457488.0,
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
}

scenario_gsa = {
    "event_name": "Gaia24amo",
    "time_of_peak": 2460418.0,
    "light_curves": [
        {
            "survey": "Gaia",
            "band": "G",
            "path": "tests/ralph/data/input/light_curves/Gaia24amo_Gaia_G.dat",
        },
        {
            "survey": "LCO",
            "band": "g",
            "path": "tests/ralph/data/input/light_curves/Gaia24amo_LCO_g.dat",
        },
        {
            "survey": "LCO",
            "band": "r",
            "path": "tests/ralph/data/input/light_curves/Gaia24amo_LCO_r.dat",
        },
        {
            "survey": "LCO",
            "band": "i",
            "path": "tests/ralph/data/input/light_curves/Gaia24amo_LCO_i.dat",
        },
    ],
}

class AnalystToolsTest:
    """
    Class to test Analyst Tools module.

    :param scenario: a scenario to test with the Analyst Tools module.

    """

    def __init__(self, scenario):
        self.scenario = scenario

    def test_find_time_of_peak(self):
        """
        Test find time of peak function.
        """

        config = {}
        config["event_name"] = self.scenario.get("event_name")
        config["light_curves"] = self.scenario.get("light_curves")

        light_curves = []
        for entry in config["light_curves"]:
            survey = entry["survey"]
            band = entry["band"]

            light_curve = input_tools.load_light_curve_from_path(entry["path"])

            light_curves.append(
                {
                    "event_name": config["event_name"],
                    "light_curve": light_curve,
                    "survey": survey,
                    "band": band,
                }
            )

        received = analyst_tools.find_time_of_peak(light_curves, 2)
        expected = self.scenario.get("time_of_peak")

        assert pytest.approx(received, 1) == pytest.approx(expected, 1)

def test_run():
    """
    Run all tests.
    """

    for case in [scenario_gaia, scenario_gsa]:
        test = AnalystToolsTest(case)
        test.test_find_time_of_peak()