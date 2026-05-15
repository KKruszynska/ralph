import json
import time

import numpy as np

from ralph.analyst import analyst_tools
from ralph.analyst.analyst import BaseAnalyst
from ralph.fitting_support import pylima


class FitAnalyst(BaseAnalyst):
    """
    Performs fitting microlensing models to one event.
    It is a subclass of the :class:`ralph.analyst.analyst.BaseAnalyst`
    It follows a flowchart specified here: link link link

    A Fit Analyst needs either a config_path or config_dict, otherwise it will not work.

    :param event_name: The name of the analyzed event.
    :type event_name: str

    :param analyst_path: A path to the folder where the input and output files with results are saved.
    :type analyst_path: str

    :param light_curves: A list containing light curves, their observatory names and filters.
    :type light_curves: list

    :param log: A logger instance started by the Event Analyst.
    :type log: logging.Logger

    :param config_dict: A dictionary with the Event Analyst configuration.
    :type config_dict: dict, optional

    :param config_path: A path to the configuration file of the Event Analyst.
    :type config_path: str, optional

     Notes on configuration:
    ------------------------------
    The configuration dictionary can contain the following keywords:

    * `ongoing_magnification_thershold`: float
        Threshold for magnification. If current magnification of the source is larger
        than the threshold, the event is considered as ongoing.
        Default value: 1.05
    * `ongoing_amplitude_thershold`: float
        Threshold for amplitude. If current amplitude of the event is above the threshold,
        the event is considered as ongoing.
        Default value: 1.0
    * `time_of_peak_bin_size`: float, in days
        Size of the bin used when binning the light curve data to look for the first
        approximation of the time of peak.
        Default value: 2.0
    * `model_fit_configuration`: dictionary
        A dictionary with configuration for specific types of models.
        Allowed models keywords are:
            - `PSPL_no_blend_no_piE` - point source-point lens model without blending and
                microlensing parallax effect;
            - `PSPL_blend_no_piE` - point source-point lens model with blending and without
                microlensing parallax effect;
            - `PSPL_no_blend_piE` - point source-point lens model without blending and with
                microlensing parallax effect;
            - `PSPL_blend_piE` - point source-point lens model with blending and
                microlensing parallax effect;
        For each model the User can specify following keywords:
            - `fitting_package` - str, name of the fitting package supported by `ralph`;
            - `fitting_method` - str, type of fitting method supported by the `fitting_package` and `ralph`;
            - `boundaries` - dict, a dictionary containing a list of keywords, and a list with two
                elements, a lower and upper limit for the given parameter:
                `key: [lower_limit, upper_limit]`
                Supported keys include:
                    - `t0` - time when the source and the lens at lowest projected separation;
                    - `u0` - impact parameter scaled by the angular Einstein radius, when the source and lens are t0;
                    - `tE` - Einstein timescale of the event;
                    - `piEN` - Northern component of the microlensing parallax vector;
                    - `piEE` - Eastern component of the microlensing parallax vector.


    """

    def __init__(self, event_name, analyst_path, light_curves, log,
                 config_dict=None, config_path=None
                 ):

        super().__init__(event_name, analyst_path, config_dict=config_dict, config_path=config_path)

        self.log = log
        self.light_curves = light_curves

        self.best_results = {}
        self.start_time = time.time()

        if config_dict is not None:
            self.parse_config(config_dict=config_dict)
            self.add_fit_config(config_dict)
        elif "fit_analyst" in self.config:
            self.parse_config(config_dict=self.config)
            self.add_fit_config(self.config)
        else:
            self.log.error("Fit Analyst: Error! Fit Analyst needs configuration parameters.")
            quit()

    def add_fit_config(self, config):
        """
        Adds Fit Analyst configuration fields to analyst's internal configuration
        dictionary.

        :param config: A dictionary with analyst's configuration parameters.
        :type config: dict
        """

        self.log.debug("Fit Analyst: Reading fit config.")

        self.config["ongoing_magnification_thershold"] = config["fit_analyst"].get(
            "ongoing_magnification_thershold", 1.05
        )
        self.config["ongoing_amplitude_thershold"] = config["fit_analyst"].get(
            "ongoing_amplitude_thershold", 1.0
        )

        self.config["top_bin_size"] = config["fit_analyst"].get(
            "time_of_peak_bin_size", 2.0
        )

        params = {}
        model_fit_config = config["fit_analyst"].get("model_fit_configuration")
        for model in model_fit_config:
            params[model] = model_fit_config.get(model)

        self.config["model_fit_configuration"] = params

        self.log.debug("Fit Analyst: Finished reading fit config.")

    def fit_pspl(
        self,
        fit_label,
        fit_name,
        starting_params,
        parallax,
        blend,
        return_norm_lc=False,
        use_boundaries=None,
    ):
        """
        Perform a point source-point lens (PSPL) fit.

        :param fit_label: The label of the model to be fitted.
        :type fit_label: str

        :param fit_name: The path of the output file.
        :type fit_name: str

        :param starting_params: Starting parameters for the fit.
        :type starting_params: list

        :param parallax: If `True`, microlensing parallax second order effect is included in the model.
        :type parallax: bool

        :param blend: If `True`, blending effect is included in the model.
        :type blend: bool

        :param return_norm_lc: If `True` all light curves aligned to a single model are returned.
        :type return_norm_lc: bool, optional

        :param use_boundaries: Boundaries for selected parameters to be used for fitting.
        :type use_boundaries: dict, optional

        :return: A list with fitted parameters and, if requested, aligned data and residuals.
        :rtype: list
        """

        self.start_time = time.time()
        results = {}

        fit_config = self.config["model_fit_configuration"].get(fit_label, None)
        if fit_config is not None:
            self.log.info("Fit Analyst: Using fitting setup specified by the User.")
            fitting_package = fit_config.get("fitting_package")
            fitting_method = fit_config.get("fitting_method", None)
            self.log.debug(f"Fit Analyst: Set up: fitting package: {fitting_package}, "
                           f"fitting method: {fitting_method}."
                           )

            boundaries = fit_config.get("boundaries", None)
            if use_boundaries is not None:
                for key in use_boundaries:
                    boundaries[key] = use_boundaries.get(key, boundaries.get(key))

            self.log.debug(f"Fit Analyst: Set up: boundaries:")
            for key in boundaries:
                self.log.debug(f"{key}: {boundaries[key]}\n")

            fitting_args = fit_config.get("fitting_method_args", None)

            if fitting_package.lower() == "pylima":
                if fitting_args is not None:
                    fit_pspl = pylima.fit_pylima.FitPylima(self.log)
                    results = fit_pspl.fit_pspl(
                        fit_name,
                        self.light_curves,
                        starting_params,
                        parallax,
                        blend,
                        return_norm_lc=return_norm_lc,
                        fitting_method=fitting_method,
                        use_boundaries=boundaries,
                        **fitting_args
                    )
                else:
                    fit_pspl = pylima.fit_pylima.FitPylima(self.log)
                    results = fit_pspl.fit_pspl(
                        fit_name,
                        self.light_curves,
                        starting_params,
                        parallax,
                        blend,
                        return_norm_lc=return_norm_lc,
                        fitting_method=fitting_method,
                        use_boundaries=boundaries,
                    )
        else:
            self.log.info("Fit Analyst: Using default fitting setup.")
            self.log.debug(f"Fit Analyst: Set up: fitting package: pyLIMA, "
                           f"fitting method: TRF."
                           )
            self.log.debug(f"Fit Analyst: Set up: boundaries:")
            for key in use_boundaries:
                self.log.debug(f"{key}: {use_boundaries[key]}\n")

            fit_pspl = pylima.fit_pylima.FitPylima(self.log)
            results = fit_pspl.fit_pspl(
                fit_name,
                self.light_curves,
                starting_params,
                parallax,
                blend,
                return_norm_lc=return_norm_lc,
                use_boundaries=use_boundaries,
            )

        self.log.debug(f"Fit Analyst: Time elapsed for fitting: {time.time() - self.start_time:.2f} s")

        return results

    def perform_ongoing_check(self):
        """
        Performs initial fit and checks if the event is ongoing.

        :return: The status of the fitting procedures, `True` if
            the process didn't encounter any exceptions, `False` otherwise.
        :rtype: bool
        """

        self.log.debug(
            f"Fit Analyst: Time elapsed for setting up the analyst: {time.time() - self.start_time:.2f} s"
        )
        self.log.info("Fit Analyst: Starting ongoing check fit.")
        self.log.info("Fit Analyst:  Find PSPL starting parameters.")

        time_of_peak = analyst_tools.find_time_of_peak(
            self.light_curves,
            self.config["top_bin_size"]
        )

        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t0": time_of_peak,
            "u0": 0.1,
            "tE": 40.0,
        }

        self.log.info("Fit Analyst: Performing PSPL fit without blend and parallax.")
        results = self.fit_pspl(
            "PSPL_no_blend_no_piE",
            self.analyst_path + "PSPL_no_blend_no_piE",
            starting_params,
            False,
            False,
            return_norm_lc=True,
        )

        fit_params_pspl_nopar = results[0]
        t_0 = fit_params_pspl_nopar["t0"]
        aligned_data, residuals = results[1], results[2]
        self.log.info("Fit Analyst:  Finished fitting.")

        # Saving the result not to perform this fit again
        self.best_results["PSPL_no_blend_no_piE"] = fit_params_pspl_nopar

        self.log.info("Fit Analyst: Identify ongoing event.")
        baseline_mag = fit_params_pspl_nopar["baseline_magnitude"]
        self.start_time = time.time()

        # todo: this currently supports only PSPL, but it should support more models,
        #  if we have them from the past. This should be consulted with the system
        #  flowchart though.

        ongoing_ampl, t_last = analyst_tools.check_ongoing_amplitude(
            self.config["ongoing_amplitude_thershold"], aligned_data, residuals, baseline_mag
        )
        ongoing_time = analyst_tools.check_ongoing_time(fit_params_pspl_nopar, t_last)
        ongoing_mag = analyst_tools.check_ongoing_magnification(
            self.config["ongoing_magnification_thershold"], fit_params_pspl_nopar, t_last
        )
        self.log.debug(f"Fit Analyst: Time of the last data point: {t_last}")
        self.log.debug(
            f"Fit Analyst: ongoing checks: ampl: {ongoing_ampl}, time: {ongoing_time}, mag: {ongoing_mag}"
        )

        ongoing = False
        if ongoing_ampl or ongoing_time or ongoing_mag:
            ongoing = True

        self.log.debug(f"Fit Analyst: Time elapsed for ongoing check: {time.time() - self.start_time:.2f} s")

        return ongoing, t_0

    def perform_ongoing_fit(self, t_0):
        """
        Performs fitting procedure for an ongoing event.
        For an ongoing event, it performs a point source-point lens model fit
        with blending and with/without parallax. Resulting models are then evaluated.
        If the best-fitting model with parallax and blending is not okay, a model without
        blending and with parallax is fitted. The results are appended to a dictionary and
        gathered for evaluation.

        :param t_0: Time of peak established by the initial fit.
        :type t_0: float
        """

        self.log.info("Fit Analyst: Starting ongoing event fit.")
        self.log.info("Fit Analyst: Finding PSPL starting parameters.")
        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t0": t_0,
            "u0": self.best_results["PSPL_no_blend_no_piE"].get("u0"),
            "tE": self.best_results["PSPL_no_blend_no_piE"].get("tE"),
        }

        self.log.info("Fit Analyst: Performing PSPL fit.")
        results = self.fit_pspl(
            "PSPL_blend_no_piE",
            self.analyst_path + "PSPL_blend_no_piE",
            starting_params,
            False,
            True,
        )
        self.best_results["PSPL_blend_no_piE"] = results

        self.log.info("Fit Analyst: Performing PSPL+piE fit.")
        starting_params["t0"] = results["t0"]
        starting_params["piEN"] = 0.0
        starting_params["piEE"] = 0.0

        self.log.info("Fit Analyst: Using default fitting setup.")
        results = self.fit_pspl(
            "PSPL_blend_piE",
            self.analyst_path + "PSPL_blend_piE",
            starting_params,
            True,
            True,
        )
        self.best_results["PSPL_blend_piE"] = results

        self.log.info("Fit Analyst: Evaluate PSPL+piE fit.")
        model_ok = self.evaluate_pspl(results)

        if not model_ok:
            self.log.info("Fit Analyst: Bad model with blending, performing PSPL+piE fit without blending.")
            results = self.fit_pspl(
                "PSPL_no_blend_piE",
                self.analyst_path + "PSPL_no_blend_piE",
                starting_params,
                True,
                False,
            )
            self.best_results["PSPL_no_blend_piE"] = results

        self.log.info("Fit Analyst: Finished fitting.")
        self.log.debug("Best models:", self.best_results)

    def perform_finished_fit_pspl(self, t_0):
        """
        Performs fitting procedure for a finished event.
        For a finished event, it performs a point source-point lens model fit
        with blending and with/without parallax. The results are appended to
        a dictionary and gathered for evaluation.

        :param t_0: Time of peak established by the initial fit.
        :type t_0: float
        """

        self.log.info("Fit Analyst: Starting finished event fit.")
        self.log.info("Fit Analyst: Finding PSPL starting parameters.")
        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t0": t_0,
            "u0": self.best_results["PSPL_no_blend_no_piE"].get("u0"),
            "tE": self.best_results["PSPL_no_blend_no_piE"].get("tE"),
        }

        self.log.info("Fit Analyst:Performing PSPL with blend fit.")
        results = self.fit_pspl(
            "PSPL_blend_no_piE",
            self.analyst_path + "PSPL_blend_no_piE",
            starting_params,
            False,
            True,
        )
        self.best_results["PSPL_blend_no_piE"] = results
        self.log.info("Fit Analyst: Finished fitting PSPL with blend fit.")

        self.log.info("Fit Analyst: Performing PSPL+piE fit.")

        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t0": self.best_results["PSPL_blend_no_piE"]["t0"],
            "u0": self.best_results["PSPL_blend_no_piE"]["u0"],
            "tE": self.best_results["PSPL_blend_no_piE"]["tE"],
            "piEN": 0.0,
            "piEE": 0.0,
        }
        sign = "p" if np.sign(starting_params["u0"]) > 0 else "n"
        self.log.info(f"Fit Analyst: Starting fitting model PSPL_blend_piE_{sign}")
        boundaries = {
            "u0": [0.0, 2.0],
            "tE": [0.0, 1000.0],
            "piEN": [-2.0, 2.0],
            "piEE": [-2.0, 2.0],
        }
        results = self.fit_pspl(
            "PSPL_blend_piE",
            self.analyst_path + "PSPL_blend_piE_" + sign,
            starting_params,
            True,
            True,
            use_boundaries=boundaries,
        )
        self.best_results["PSPL_blend_piE_" + sign] = results

        self.log.info(f"Fit Analyst:  Finished fitting model PSPL_blend_piE_{sign}")

        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t0": self.best_results["PSPL_blend_piE_" + sign]["t0"],
            "u0": -1 * self.best_results["PSPL_blend_piE_" + sign]["u0"],
            "tE": self.best_results["PSPL_blend_piE_" + sign]["tE"],
            "piEN": self.best_results["PSPL_blend_piE_" + sign]["piEN"],
            "piEE": self.best_results["PSPL_blend_piE_" + sign]["piEE"],
        }
        sign = "p" if np.sign(starting_params["u0"]) > 0 else "n"
        self.log.info(f"Fit Analyst: Starting fitting model PSPL_blend_piE_{sign}")

        boundaries["u0"] =  [-2.0, 0.0]

        results = self.fit_pspl(
            "PSPL_blend_piE",
            self.analyst_path + "PSPL_blend_piE_" + sign,
            starting_params,
            True,
            True,
            use_boundaries=boundaries,
        )
        self.best_results["PSPL_blend_piE_" + sign] = results

        self.log.info(f"Fit Analyst:  Finished fitting model PSPL_blend_piE_{sign}")

    def evaluate_pspl(self, model_params):
        """
        Checks if best-fitting solution for a particular model has Einstein timescale, source magnitude,
        and, if available, blend magnitude within three-sigma.
        Lifted from mop.toolbox.fittols.test_quality_of_model_fit

        :param model_params: Best-fitting model parameters.
        :type: dict

        :return: `True` if Einstein timescale tE, source magnitude, and, if available, blending magnitude
            are within three-sigma , `False` otherwise.
        :rtype: bool
        """
        fit_ok = True

        blend_check = False
        if "blend_magnitude" in model_params:
            blend_check = (
                np.abs(model_params["blend_magnitude"]) < 3.0 * model_params["blend_mag_error"]
            )

        source_check = (
            np.abs(model_params["source_magnitude"]) < 3.0 * model_params["source_mag_error"]
        )

        te_check = np.abs(model_params["tE"]) < 3.0 * model_params["tE_error"]
        if blend_check or source_check or te_check:
            fit_ok = False

        return fit_ok

    def perform_fit(self):
        """
        Perform fitting procedures according to the flowchart found in here [link link link].

        :return: A dictionary with all found best-fitting solutions for all tested models.
        :rtype: dict
        """

        self.log.debug("Fit Analyst: Performing a fit.")
        ongoing, t_0 = self.perform_ongoing_check()

        self.log.debug(f"Fit Analyst: Event identified as ongoing? {ongoing}.")
        if ongoing:
            self.log.info("Fit Analyst: Performing an ongoing fit.")
            self.perform_ongoing_fit(t_0)
            # perform model evaluation here
            # perform anomaly finder on best model

        else:
            self.log.info("Fit Analyst: Performing a finished event fit.")
            self.perform_finished_fit_pspl(t_0)
            # perform model evaluation here
            # perform anomaly finder on best model
            # if anomaly: perform_finished_fit_multiple()
            # else if peak covered: perform_finished_FSPL()
            # evaluate models
            # anomaly finder

        self.log.debug("Fit Analyst: Best models:")
        for model in self.best_results:
            params = self.best_results[model]
            if "piEN" in params:
                self.log.debug(
                    f"Fit Analyst: {model:s} : \n"
                    f"t0={params["t0"]:.2f}, u0={params["u0"]:.2f}, tE={params["tE"]:.2f}, \n"
                    f"piEN={params["piEN"]:.2f}, piEE={params["piEE"]:.2f}\n"
                )
            else:
                self.log.debug(
                    f"Fit Analyst: {model:s} : \n"
                    f"t0={params["t0"]:.2f}, u0={params["u0"]:.2f}, tE={params["tE"]:.2f}, \n"
                )

        # Save results
        self.log.debug("Fit Analyst: Saving results.")
        # Save results to a file
        file_name = self.analyst_path + "fit_results.json"
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(self.best_results, file, ensure_ascii=False, indent=4)
        self.log.debug(f"Fit Analyst: Results saved to {file_name:s}.")

        # Save best results statistics
        file_name = self.analyst_path + "fit_stats.txt"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(
                f"{"# name":<20s} : {"chi2":<7s} {"red_chi2":<7s}"
                f"{"SW":<7s} {"AD":<7s} {"KS":<7s} {"AIC":<7s} {"BIC":<7s}\n"
            )
            file.write("#--------------------------------------------------------------------------------\n")
            for model in self.best_results:
                params = self.best_results[model]
                file.write(
                    f"{model:20s} : {params["chi2"]:7.2f} {params["red_chi2"]:7.2f}"
                    f"{params["sw_test"]:7.2f} {params["ad_test"]:7.2f} {params["ks_test"]:7.2f}"
                    f"{params["aic_test"]:7.2f} {params["bic_test"]:7.2f}\n"
                )

        return self.best_results
