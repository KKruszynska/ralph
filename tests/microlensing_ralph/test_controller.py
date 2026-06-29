import json
import os
from pathlib import Path

import numpy as np
import pytest

from microlensing_ralph.controller.controller import Controller

ralph_tests_home = os.path.join("tests", "microlensing_ralph", "data")

class ControllerPathsTest:
    """
    Tests to check if controller works for a finished event.
    """

    def __init__(self, expected_results):
        self.expected_results = expected_results

    def test_launch_analysts(self):
        """
        Run controller to check if it works.
        """
        event_list = [
            "GDR3_ULENS_025",
        ]

        config = {
            "python_compiler": "python",
            "group_processing_limit": 2,
            "events_path": os.path.join(ralph_tests_home, "input", "controller"),
            "software_dir": os.path.join("src", "microlensing_ralph", "analyst"),
            "config_type": "yaml",
            "log_stream": False,
            "log_location": os.path.join(ralph_tests_home, "output", "controller_launch"),
            "log_level": "debug",
        }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()

        # Check if expected files exist
        # Controller log
        controller_log_path = os.path.join(ralph_tests_home, "output", "controller_launch")
        output = Path(os.path.join(controller_log_path, "controller.log"))
        assert output.exists() is True
        assert output.is_file() is True

        # Analyst output files
        analyst_home = os.path.join(ralph_tests_home, "input", "controller")
        for event in event_list:
            analyst_path = os.path.join(analyst_home, event)

            output = Path(analyst_path)
            assert output.exists() is True
            assert output.is_dir() is True

            output = Path(os.path.join(analyst_path, "fit_results.json"))
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(os.path.join(analyst_path, "fit_stats.txt"))
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(os.path.join(analyst_path, event + "_analyst.log"))
            assert output.exists() is True
            assert output.is_file() is True

            model_plots = [
                "PSPL_no_blend_no_piE",
                "PSPL_blend_no_piE",
                "PSPL_blend_piE_p",
                "PSPL_blend_piE_n",
            ]

            for file_path in model_plots:
                output = Path(os.path.join(analyst_path, file_path + ".html"))
                assert output.exists() is True
                assert output.is_file() is True

            bands = [
                "_CMD_Gaia_DR3_Gaia_G",
                "_CMD_Gaia_DR3_Gaia_BP",
                "_CMD_Gaia_DR3_Gaia_RP",
            ]
            for model in model_plots:
                for band in bands:
                    output = Path(os.path.join(analyst_path, event + "_" + model + band + ".html"))
                    assert output.exists() is True
                    assert output.is_file() is True

            expected_result_path = self.expected_results[event]
            with open(expected_result_path, "r") as file:
                expected_fit_result = json.load(file)

            with open(os.path.join(analyst_path, "fit_results.json"), "r") as file:
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

    def __init__(self, expected_results):
        self.expected_results = expected_results

    def test_launch_analysts(self):
        """
        Run controller to check if it works.
        """

        event_list = ["AT2024kwu", "Gaia18cbf", "GDR3_ULENS_018"]

        config = {
            "python_compiler": "python",
            "group_processing_limit": 2,
            "config_type": "yaml",
            "events_path": os.path.join(ralph_tests_home, "input", "controller"),
            "software_dir": os.path.join("src", "microlensing_ralph", "analyst"),
            "log_stream": False,
            "log_location": os.path.join(ralph_tests_home, "output", "controller_analysts"),
            "log_level": "debug",
        }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()

        # Check if expected files exist
        # Controller log
        controller_log_path = os.path.join(ralph_tests_home, "output", "controller_analysts")
        output = Path(os.path.join(controller_log_path, "controller.log"))
        assert output.exists() is True
        assert output.is_file() is True

        # Analyst output files
        analyst_home = os.path.join(ralph_tests_home, "input", "controller")
        for event in event_list:
            analyst_path = os.path.join(analyst_home, event)

            output = Path(analyst_path)
            assert output.exists() is True
            assert output.is_dir() is True

            output = Path(os.path.join(analyst_path, "fit_results.json"))
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(os.path.join(analyst_path, "fit_stats.txt"))
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(os.path.join(analyst_path, event + "_analyst.log"))
            assert output.exists() is True
            assert output.is_file() is True

            if event == "AT2024kwu":
                model_plots = [
                    "PSPL_no_blend_no_piE",
                    "PSPL_blend_no_piE",
                    "PSPL_blend_piE",
                ]
            else:
                model_plots = [
                    "PSPL_no_blend_no_piE",
                    "PSPL_blend_no_piE",
                    "PSPL_blend_piE_p",
                    "PSPL_blend_piE_n",
                ]

            for file_path in model_plots:
                output = Path(os.path.join(analyst_path, file_path + ".html"))
                assert output.exists() is True
                assert output.is_file() is True

            expected_result_path = self.expected_results.get(event, None)
            if expected_result_path is not None:
                with open(expected_result_path, "r") as file:
                    expected_fit_result = json.load(file)

                with open(os.path.join(analyst_path, "fit_results.json"), "r") as file:
                    received_fit_result = json.load(file)

                for model in expected_fit_result:
                    model_result = received_fit_result[model]
                    expected_result = expected_fit_result[model]
                    for key in expected_result:
                        if "error" not in key:
                            expected = float(expected_result[key])
                            received = float(model_result[key])
                            if not np.isnan(expected):
                                assert pytest.approx(received, 2) == pytest.approx(expected, 2)


def test_run():
    """
    Run all tests.
    """

    expected_fit_results = {
        "GDR3_ULENS_025": os.path.join(ralph_tests_home, "input", "test_results", "gdr3_ulens_025_fit_results.json"),
        "GDR3_ULENS_018": os.path.join(ralph_tests_home, "input", "test_results", "gdr3_ulens_018_fit_results.json"),
    }

    test = ControllerPathsTest(expected_fit_results)
    test.test_launch_analysts()

    test = ControllerPathsOngoingTest(expected_fit_results)
    test.test_launch_analysts()

    controller_log_path = [
        os.path.join(ralph_tests_home, "output", "controller_launch"),
        os.path.join(ralph_tests_home, "output", "controller_analysts"),
    ]

    for controller_path in controller_log_path:
        output = Path(os.path.join(controller_path, "controller.log"))
        if output.exists():
            os.remove(output)

    analyst_home = os.path.join(ralph_tests_home, "input", "controller")

    test_events = [
        "AT2024kwu",
        "GDR3_ULENS_018",
        "GDR3_ULENS_025",
        "Gaia18cbf",
    ]

    for event in test_events:
        analyst_path = os.path.join(analyst_home, event)

        output = Path(os.path.join(analyst_path, "fit_results.json"))
        if output.exists():
            os.remove(output)

        output = Path(os.path.join(analyst_path,  "fit_stats.txt"))
        if output.exists():
            os.remove(output)

        fpath = os.path.join(analyst_path, event + "_analyst.log")
        output = Path(fpath)
        if output.exists():
            os.remove(output)

        model_plots = [
            "PSPL_no_blend_no_piE",
            "PSPL_blend_no_piE",
            "PSPL_blend_piE",
            "PSPL_blend_piE_p",
            "PSPL_blend_piE_n",
            "PSPL_no_blend_piE",
            "PSPL_no_blend_piE_p",
            "PSPL_no_blend_piE_n"
        ]

        for file_path in model_plots:
            output = Path(os.path.join(analyst_path, file_path + ".html"))
            if output.exists():
                os.remove(output)

        bands = [
            "_CMD_Gaia_DR3_Gaia_G",
            "_CMD_Gaia_DR3_Gaia_BP",
            "_CMD_Gaia_DR3_Gaia_RP",
        ]
        for model in model_plots:
            for band in bands:
                output = Path(os.path.join(analyst_path, event + "_" + model + band + ".html"))
                if output.exists():
                    os.remove(output)
