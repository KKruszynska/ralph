import json
import os
from pathlib import Path

import numpy as np
import pytest

from ralph.controller.controller import Controller

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
            "GaiaDR3_ULENS_025",
        ]

        config = {
            "python_compiler": "python",
            "group_processing_limit": 2,
            "events_path": "tests/ralph/data/input/controller/",
            "software_dir": "src/ralph/analyst/",
            "config_type": "yaml",
            "log_stream": False,
            "log_location": "tests/ralph/data/output/controller_launch/",
            "log_level": "debug",
        }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()

        # Check if expected files exist
        # Controller log
        controller_log_path = "tests/ralph/data/output/controller_launch/"
        output = Path(controller_log_path + "controller.log")
        assert output.exists() is True
        assert output.is_file() is True

        # Analyst output files
        analyst_home = "tests/ralph/data/input/controller/"
        for event in event_list:
            analyst_path = analyst_home + event

            output = Path(analyst_path)
            assert output.exists() is True
            assert output.is_dir() is True

            output = Path(analyst_path + "/fit_results.json")
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + "/fit_stats.txt")
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + "/" + event + "_analyst.log")
            assert output.exists() is True
            assert output.is_file() is True

            model_plots = [
                "PSPL_no_blend_no_piE",
                "PSPL_blend_no_piE",
                "PSPL_blend_piE_p",
                "PSPL_blend_piE_m",
            ]

            for file_path in model_plots:
                output = Path(analyst_path + "/" + file_path + ".html")
                assert output.exists() is True
                assert output.is_file() is True

            bands = [
                "_CMD_Gaia_DR3_Gaia_G",
                "_CMD_Gaia_DR3_Gaia_BP",
                "_CMD_Gaia_DR3_Gaia_RP",
            ]
            for model in model_plots:
                for band in bands:
                    output = Path(analyst_path + "/" + event + "_" + model + band + ".html")
                    assert output.exists() is True
                    assert output.is_file() is True

            expected_result_path = self.expected_results[event]
            with open(expected_result_path, "r") as file:
                expected_fit_result = json.load(file)

            with open(analyst_path + "/fit_results.json", "r") as file:
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

        event_list = ["AT2024kwu", "Gaia18cbf", "GaiaDR3_ULENS_018"]

        config = {
            "python_compiler": "python",
            "group_processing_limit": 2,
            "config_type": "yaml",
            "events_path": "tests/ralph/data/input/controller/",
            "software_dir": "src/ralph/analyst/",
            "log_stream": False,
            "log_location": "tests/ralph/data/output/controller_analysts/",
            "log_level": "debug",
        }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()

        # Check if expected files exist
        # Controller log
        controller_log_path = "tests/ralph/data/output/controller_analysts/"
        output = Path(controller_log_path + "controller.log")
        assert output.exists() is True
        assert output.is_file() is True

        # Analyst output files
        analyst_home = "tests/ralph/data/input/controller/"
        for event in event_list:
            analyst_path = analyst_home + event

            output = Path(analyst_path)
            assert output.exists() is True
            assert output.is_dir() is True

            output = Path(analyst_path + "/fit_results.json")
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + "/fit_stats.txt")
            assert output.exists() is True
            assert output.is_file() is True

            output = Path(analyst_path + "/" + event + "_analyst.log")
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
                    "PSPL_blend_piE_m",
                ]

            for file_path in model_plots:
                output = Path(analyst_path + "/" + file_path + ".html")
                assert output.exists() is True
                assert output.is_file() is True

            expected_result_path = self.expected_results.get(event, None)
            if expected_result_path is not None:
                with open(expected_result_path, "r") as file:
                    expected_fit_result = json.load(file)

                with open(analyst_path + "/fit_results.json", "r") as file:
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
        "GaiaDR3_ULENS_025": "tests/ralph/data/input/test_results/gdr3_ulens_025_fit_results.json",
        "GaiaDR3_ULENS_018": "tests/ralph/data/input/test_results/gdr3_ulens_018_fit_results.json",
    }

    test = ControllerPathsTest(expected_fit_results)
    test.test_launch_analysts()

    test = ControllerPathsOngoingTest(expected_fit_results)
    test.test_launch_analysts()

    controller_log_path = [
        "tests/ralph/data/output/controller_launch/",
        "tests/ralph/data/output/controller_analysts/",
    ]

    for controller_path in controller_log_path:
        output = Path(controller_path + "controller.log")
        if output.exists():
            os.remove(output)

    analyst_home = "tests/ralph/data/input/controller/"

    test_events = [
        "GaiaDR3_ULENS_018",
        "GaiaDR3_ULENS_025",
        "AT2024kwu",
        "Gaia18cbf",
    ]

    for event in test_events:
        analyst_path = analyst_home + event

        output = Path(analyst_path + "/fit_results.json")
        if output.exists():
            os.remove(output)

        output = Path(analyst_path + "/fit_stats.txt")
        if output.exists():
            os.remove(output)

        output = Path(analyst_path + "/" + event + "_analyst.log")
        if output.exists():
            os.remove(output)

        model_plots = [
            "PSPL_no_blend_no_piE",
            "PSPL_blend_no_piE",
            "PSPL_blend_piE",
            "PSPL_blend_piE_p",
            "PSPL_blend_piE_m",
        ]

        for file_path in model_plots:
            output = Path(analyst_path + "/" + file_path + ".html")
            if output.exists():
                os.remove(output)

        bands = [
            "_CMD_Gaia_DR3_Gaia_G",
            "_CMD_Gaia_DR3_Gaia_BP",
            "_CMD_Gaia_DR3_Gaia_RP",
        ]
        for model in model_plots:
            for band in bands:
                output = Path(analyst_path + "/" + event + "_" + model + band + ".html")
                if output.exists():
                    os.remove(output)
