import os
from pathlib import Path

import pytest

from ralph.fitting_support.pylima.fit_pylima import FitPylima
from ralph.toolbox import input_tools, logs

scenario = {
    "event_name": "GaiaDR3_ULENS_025",
    "ra": 260.8781,
    "dec": -27.3788,
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


class TestPylima:
    """
    Testing pyLIMA fitting implementation.
    """

    def __init__(self, scenario):
        self.ra = scenario["ra"]
        self.dec = scenario["dec"]
        light_curves = []
        for lc in scenario["light_curves"]:
            lc_dict = {}
            lc_dict["survey"] = lc["survey"]
            lc_dict["band"] = lc["band"]

            if "ephemeris" in lc:
                lc_dict["ephemeris"] = input_tools.load_ephemeris_from_path(
                    lc["ephemeris"],
                    # skip_header = 94,
                    # skip_footer = 4159,
                    usecols=(0, 1, 2, 3),
                )

            data = input_tools.load_light_curve_from_path(lc["path"])

            lc_dict["light_curve"] = data

            light_curves.append(lc_dict)

        self.light_curves = light_curves
        self.event_name = scenario["event_name"]

    def test_create_event(self):
        """
        Test setting up event instance with pyLIMA.
        """
        log = logs.start_log("tests/ralph/data/output/pyLIMA/", "debug", event_name="test_pylima_fits_event")

        event_name = self.event_name

        log.info("Creating FitPylima instance.")
        fit_pspl = FitPylima(log)
        log.info("Setting up event.")

        event = fit_pspl.setup_event(event_name, self.ra, self.dec, self.light_curves)

        log.info("Event set up.")
        logs.close_log(log)

        assert event.name == event_name
        assert event.ra == self.ra
        assert event.dec == self.dec

    def test_fit_pspl(self):
        """
        Test fitting with pyLIMA for PSPL without secondary effects.
        """
        log = logs.start_log("tests/ralph/data/output/pyLIMA/", "debug", event_name="test_pylima_fits_pspl")

        fit_pspl = FitPylima(log)
        log.info("Fitting event.")
        starting_params = {
            "ra": self.ra,
            "dec": self.dec,
            "t0": 2457492.0,
            "u0": 0.1,
            "tE": 40.0,
        }

        params = fit_pspl.fit_pspl("PSPL_no_piE", self.light_curves, starting_params, False, True)

        log.info("Fitting finished.")
        log.debug(
            f"Fitted parameters: t_0 = {params['t0']:.2f} +- {params['t0_error']:.2f},  \n"
            f"u_0 = {params['u0']:.3f} +- {params['u0_error']:.3f},  \n"
            f"t_E = {params['tE']:.2f} +- {params['tE_error']:.2f}\n"
        )

        assert pytest.approx(params["t0"], abs=0.01) == 2457491.75
        assert pytest.approx(params["u0"], abs=0.01) == 0.194
        assert pytest.approx(params["tE"], abs=0.01) == 120.81
        logs.close_log(log)

    def test_fit_parallax(self):
        """
        Testing pylima parallax model fit implementation.
        """
        log = logs.start_log("tests/ralph/data/output/pyLIMA/", "debug", event_name="test_pyLIMA_fits_pie")

        fit_pspl = FitPylima(log)
        log.info("Fitting event.")
        starting_params = {
            "ra": self.ra,
            "dec": self.dec,
            "t0": 2457492.0,
            "u0": 0.1,
            "tE": 40.0,
            "piEN": 0.0,
            "piEE": 0.0,
        }

        params = fit_pspl.fit_pspl("PSPL_piE", self.light_curves, starting_params, True, True)

        log.info("Fitting finished.")
        log.debug(
            f"Fitted parameters: t_0 = {params['t0']:.2f} +- {params['t0_error']:.2f}, \n"
            f"u_0 = {params['u0']:.3f} +- {params['u0_error']:.3f}, \n"
            f"t_E = {params['tE']:.2f} +- {params['tE_error']:.2f}, \n"
            f"piEN = {params['piEN']:.3f} +- {params['piEN_error']:.3f}, \n"
            f"piEE = {params['piEE']:.3f} +- {params['piEE_error']:.3f}\n"
        )

        assert pytest.approx(params["t0"], abs=0.01) == 2457487.76
        assert pytest.approx(params["u0"], abs=0.01) == 0.119
        assert pytest.approx(params["tE"], abs=0.01) == 176.20
        assert pytest.approx(params["piEN"], abs=0.01) == 0.582
        assert pytest.approx(params["piEE"], abs=0.01) == 0.305

        logs.close_log(log)


def test_run():
    """
    Run pylima fitting tests.
    """

    test = TestPylima(scenario)
    test.test_create_event()
    test.test_fit_pspl()
    test.test_fit_parallax()

    analyst_path = "tests/ralph/data/output/pyLIMA/"
    event_names = ["test_pyLIMA_fits_pie", "test_pylima_fits_event", "test_pylima_fits_pspl"]

    for event in event_names:
        output = Path(analyst_path + event + "_analyst.log")
        if output.exists():
            os.remove(output)
