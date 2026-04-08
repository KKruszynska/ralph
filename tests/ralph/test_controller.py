import glob, os
import numpy as np
import pandas as pd
import json

import pytest


class TestControllerPaths:
    '''
    Tests to check if controller works fine.
    '''

    def test_launch_analysts(self):
        from MFPipeline.controller.controller import Controller

        event_list = [#"GaiaDR3-ULENS-018",
                      "GaiaDR3-ULENS-025"
                      ]
        config = {
            "python_compiler": "python",
            "group_processing_limit": 1,
            "events_path":
                "tests/test_controller/",
            "software_dir":
                "MFPipeline/analyst/",
            "config_type": "yaml",
            "log_stream": False,
            "log_location":
                "tests/test_controller/",
            "log_level": "debug"
            }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()

# class TestControllerDicts:
#     '''
#     Tests to check if controller works fine.
#     '''
#
#     def test_launch_analysts(self):
#         from MFPipeline.controller.controller import Controller
#
#
#
#         event_list = ["GaiaDR3-ULENS-018",
#                       "GaiaDR3-ULENS-025",
#                       ]
#
#         event_info = pd.read_csv("tests/test_controller/events_info.csv", header=0)
#
#         analyst_jsons = {}
#         path_lightcurves = "tests/test_controller/light_curves/"
#         os.chdir(path_lightcurves)
#         for event in event_list:
#             dictionary = {}
#             idx = event_info.index[event_info["#event_name"] == event].tolist()
#             dictionary["event_name"] = event
#             dictionary["ra"], dictionary["dec"] = "%f"%event_info["ra"].values[idx][0], "%f"%event_info["dec"].values[idx][0]
#             dictionary["lc_analyst"] = {}
#             dictionary["lc_analyst"]["n_max"] = "%d"%event_info["lc_nmax"].values[idx][0]
#             dictionary["fit_analyst"] = {}
#             dictionary["fit_analyst"]["fitting_package"] = "pyLIMA"
#
#             # cats = event_info["catalogues"].values[idx][0].split(" ")
#             # cat_list = []
#             # for catalogue in cats:
#             #     dict = {}
#             #     dict["name"] = catalogue
#             #     dict["bands"] = event_info["bands"].values[idx][0].split(" ")
#             #     if (len(event_info["path"].values[idx]) > 0):
#             #         dict["cmd_path"] = event_info["path"].values[idx][0]
#             #         dict["cmd_separator"] = ","
#             #     cat_list.append(dict)
#             # dictionary["cmd_analyst"] = {}
#             # dictionary["cmd_analyst"]["catalogues"] = cat_list
#
#             light_curves = []
#             for file in glob.glob("*%s*.dat" % event):
#                 light_curve = np.genfromtxt(file, usecols=(0, 1, 2), unpack=True)
#                 light_curve = light_curve.T
#
#                 survey = ""
#                 band = ""
#                 if ("mod" in file):
#                     survey = "Gaia"
#                     txt = file.split(".")
#                     band = txt[0].split("_")[-1]
#                     light_curve[:, 0] = light_curve[:, 0] + 2450000.
#                 elif ("OGLE" in file):
#                     survey = "OGLE"
#                     band = "I"
#                 elif ("KMT" in file):
#                     survey = "KMTNet_" + file[-7]
#                     band = "I"
#
#                 dict = {
#                     "survey": survey,
#                     "band": band,
#                     "lc": json.dumps(light_curve.tolist())
#                 }
#                 light_curves.append(dict)
#
#             dictionary["light_curves"] = light_curves
#             js = json.dumps(dictionary)
#             analyst_jsons[event] = js
#
#         os.chdir("../../../")
#         config = {
#             "python_compiler": "python",
#             "group_processing_limit": 3,
#             "events_path": "tests/test_controller/",
#             "software_dir": "MFPipeline/analyst/",
#             "log_stream": False,
#             "log_location":
#                 "tests/test_controller/",
#             "log_level": "debug"
#             }
#
#         controller = Controller(event_list, config_dict=config, analyst_dicts=analyst_jsons)
#         controller.launch_analysts()


# class TestControllerOngoing:
#     '''
#     Tests to check if controller works fine.
#     '''
#
#     def test_launch_analysts(self):
#         from MFPipeline.controller.controller import Controller
#
#         # event_list = ["Gaia24amo", "Gaia24cbz", "AT2024kwu", "GaiaDR3-ULENS-018",
#         #               "GaiaDR3-ULENS-025"]
#
#         # event_list = ["Gaia24amo", "AT2024kwu", "GaiaDR3-ULENS-018"]
#         event_list = ["Gaia24amo"]
#
#         coordinates = {
#             "Gaia24amo": {
#                 "ra": 249.14892083,
#                 "dec": -53.74991944,
#             },
#             "Gaia24cbz": {
#                 "ra": 251.87178,
#                 "dec": -47.20051,
#             },
#             "AT2024kwu": {
#                 "ra": 102.93358333,
#                 "dec": 44.352166666,
#             },
#             "GaiaDR3-ULENS-018": {
#                 "ra": 271.119,
#                 "dec": -29.8162,
#             },
#             "GaiaDR3-ULENS-025": {
#                 "ra": 260.8781,
#                 "dec": -27.3788,
#             },
#         }
#
#         analyst_jsons = {}
#         path_lightcurves = "./examples/light_curves/"
#         # path_lightcurves = "../examples/light_curves/"
#         os.chdir(path_lightcurves)
#
#         for event in event_list:
#             dictionary = {
#                 "event_name": event,
#                 "ra": "%f" % coordinates[event]["ra"],
#                 "dec": "%f" % coordinates[event]["dec"],
#                 "lc_analyst": {
#                     "n_max": 10,
#                 },
#             "fit_analyst": {
#                 "fitting_package": "pyLIMA",
#                 }
#             }
#
#             light_curves = []
#             for file in glob.glob("*%s*.dat" % event):
#                 light_curve = np.genfromtxt(file, usecols=(0, 1, 2), unpack=True)
#                 light_curve = light_curve.T
#
#                 survey = ""
#                 band = ""
#
#                 if "GSA" in file:
#                     survey = "Gaia"
#                     txt = file.split(".")
#                     band = txt[0].split("_")[-1]
#                 elif "LCO" in file:
#                     survey = "LCO"
#                     txt = file.split(".")
#                     band = txt[0].split("_")[-1]
#                 elif "ZTF" in file:
#                     survey = "ZTF"
#                     txt = file.split(".")
#                     band = txt[0].split("_")[-1]
#                 elif "ATLAS" in file:
#                     survey = "ATLAS"
#                     txt = file.split(".")
#                     band = txt[0].split("_")[-1]
#                 elif ("mod" in file):
#                     survey = "Gaia"
#                     txt = file.split(".")
#                     band = txt[0].split("_")[-1]
#                     light_curve[:, 0] = light_curve[:, 0] + 2450000.
#                 elif ("OGLE" in file):
#                     survey = "OGLE"
#                     band = "I"
#                 elif ("KMT" in file):
#                     survey = "KMTNet_" + file[-7]
#                     band = "I"
#                     light_curve[:, 0] = light_curve[:, 0] + 2450000.
#
#                 lc_dict = {
#                     "survey": survey,
#                     "band": band,
#                     "lc": json.dumps(light_curve.tolist())
#                 }
#                 light_curves.append(lc_dict)
#
#             dictionary["light_curves"] = light_curves
#             file_name = "../../tests/test_controller_ongoing/" + "%s.json" % (event)
#             with open(file_name, "w", encoding="utf-8") as file:
#                 json.dump(dictionary, file, ensure_ascii=False, indent=4)
#             js = json.dumps(dictionary)
#             analyst_jsons[event] = js
#
#
#         path_lightcurves = "../../"
#         os.chdir(path_lightcurves)
#
#         config = {
#             "python_compiler": "python",
#             "group_processing_limit": 1,
#             "events_path":
#                 "tests/test_controller_ongoing/",
#             "software_dir":
#                 "MFPipeline/analyst/",
#             "log_stream": False,
#             "log_location":
#                 "tests/test_controller_ongoing/",
#             "log_level": "debug"
#         }
#
#         controller = Controller(event_list, config_dict=config, analyst_dicts=analyst_jsons)
#         controller.launch_analysts()

class TestControllerPathsOngoing:
    '''
    Tests to check if controller works fine.
    '''

    def test_launch_analysts(self):
        from MFPipeline.controller.controller import Controller

        # event_list = ["Gaia24amo", "Gaia24cbz", "AT2024kwu", "GaiaDR3_ULENS_018",
        #               "GaiaDR3_ULENS_025"]

        event_list = ["AT2024kwu", "GaiaDR3-ULENS-018"]

        config = {
            "python_compiler": "python",
            "group_processing_limit": 2,
            "config_type": "json",
            "events_path":
                "tests/test_controller_path/",
            "software_dir":
                "MFPipeline/analyst/",
            "log_stream": False,
            "log_location":
                "tests/test_controller_path/",
            "log_level": "debug"
        }

        controller = Controller(event_list, config_dict=config)
        controller.launch_analysts()