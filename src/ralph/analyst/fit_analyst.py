import json
import time

import numpy as np

from ralph.analyst import analyst_tools
from ralph.analyst.analyst import Analyst
from ralph.fitting_support import pylima


class FitAnalyst(Analyst):
    """
    Performs fitting microlensing models to one event.
    It is a subclass of the :class:`ralph.analyst.analyst.Analyst`
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
            self.parse_config(config_dict)
            self.add_fit_config(config_dict)
        elif "fit_analyst" in self.config:
            self.parse_config(self.confing)
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

        self.config["fitting_package"] = config["fit_analyst"]["fitting_package"]
        self.config["ongoing_magnification_thershold"] = config["fit_analyst"].get(
            "ongoing_magnification_thershold", 1.05
        )
        self.config["ongoing_amplitude_thershold"] = config["fit_analyst"].get(
            "ongoing_amplitude_thershold", 1.0
        )

        params = {}
        model_fit_config = config["fit_analyst"].get("model_fit_configuration")
        for model in model_fit_config:
            params[model] = model_fit_config.get(model)

        self.config["model_fit_configuration"] = params

        self.log.debug("Fit Analyst: Finished reading fit config.")

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
        self.log.info("Find PSPL starting parameters.")
        time_of_peak = analyst_tools.find_time_of_peak(self.light_curves)
        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t_0": time_of_peak,
            "u_0": 0.1,
            "t_E": 40.0,
        }

        self.log.info("Perform PSPL fit without blend and parallax.")
        if self.config["fitting_package"].lower() == "pylima":
            fitting_routine = (
                self.config["model_fit_configuration"]["PSPL_no_blend_no_piE"].get("fitting_routine")
            )
            use_boundaries = (
                self.config["model_fit_configuration"]["PSPL_no_blend_no_piE"].get("boundaries", None)
            )
            results = self.fit_pspl(
                self.analyst_path + "PSPL_no_blend_no_piE",
                starting_params,
                False,
                False,
                return_norm_lc=True,
                use_boundaries=use_boundaries,
                fitting_method=fitting_routine,
            )
        else:
            results = self.fit_pspl(
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

        self.log.info("Identify ongoing event.")
        baseline_mag = fit_params_pspl_nopar["baseline_magnitude"]
        self.start_time = time.time()

        # todo: this currently supports only PSPL, but it should support more models, if we have them from the
        # todo: past. This should be consulted with the system flowchart though.

        ongoing_ampl, t_last = analyst_tools.check_ongoing_amplitude(
            self.config["ongoing_amplitude_thershold"], aligned_data, residuals, baseline_mag
        )
        ongoing_time = analyst_tools.check_ongoing_time(fit_params_pspl_nopar, t_last)
        ongoing_mag = analyst_tools.check_ongoing_magnification(
            self.config["ongoing_magnification_thershold"], fit_params_pspl_nopar, t_last
        )

        self.log.debug(
            f"Fit Analyst: ongoing checks: ampl: {ongoing_ampl}, time: {ongoing_time}, mag: {ongoing_mag}"
        )

        ongoing = False
        if ongoing_ampl or ongoing_time or ongoing_mag:
            ongoing = True

        self.log.debug(f"Fit Analyst: Time elapsed for ongoing check: {time.time() - self.start_time:.2f} s")

        return ongoing, t_0

    def fit_pspl(
        self,
        fit_name,
        starting_params,
        parallax,
        blend,
        return_norm_lc=False,
        use_boundaries=None,
        fitting_method=None,
    ):
        """
        Perform a Point Source Point Lens fit.

        :param fit_name: str, label of the fit
        :param starting_params: list, starting parameters for the fit
        :param parallax: boolean, use parallax?
        :param blend: boolean, should blending be fitted?
        :param return_norm_lc: boolean, optional, should the fit returned the aligned light curves?
        :param use_boundaries: dictionary, optional, contains boundaries to be used for fitting
        :param fitting_method: str, optional, fitting method to use

        :return: list with fitted parameters and if requested, aligned data
        """

        self.start_time = time.time()
        results = {}
        if self.config["fitting_package"].lower() == "pylima":
            if fitting_method is not None:
                self.log.debug(f"Fit Analyst: Using fitting method: {fitting_method}")
                fit_pspl = pylima.fit_pylima.FitPylima(self.log)
                results = fit_pspl.fit_pspl(
                    fit_name,
                    self.light_curves,
                    starting_params,
                    parallax,
                    blend,
                    return_norm_lc=return_norm_lc,
                    use_boundaries=use_boundaries,
                    fitting_method=fitting_method,
                )
            else:
                self.log.debug("Fit Analyst: Using default fitting method")
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

    def perform_ongoing_fit(self, t_0):
        """
        Perform fitting procedure for an ongoing event.
        According to the Software Requirements, the analyst
        has to perform PSPL fit with blending and with/without parallax.
        Then they are evaluated. If the blend fit is not okay, fit without
        blend is performed. The results are appended to a dictionary and
        gathered for evaluation.
        """

        self.log.info("Fit Analyst: Starting ongoing event fit.")
        self.log.info("Find PSPL starting parameters.")
        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t_0": t_0,
            "u_0": 0.1,
            "t_E": 40.0,
        }

        self.log.info("Perform PSPL fit.")
        fitting_routine = (
            self.config["model_fit_configuration"]["PSPL_blend_no_piE"].get("fitting_routine")
        )
        use_boundaries = (
            self.config["model_fit_configuration"]["PSPL_blend_no_piE"].get("boundaries", None)
        )
        results = self.fit_pspl(
            self.analyst_path + "PSPL_blend_no_piE",
            starting_params,
            False,
            True,
            fitting_method=fitting_routine,
            use_boundaries=use_boundaries,
        )
        self.best_results["PSPL_blend_no_piE"] = results

        self.log.info("Evaluate PSPL fit.")

        self.log.info("Perform PSPL+piE fit.")
        starting_params["t_0"] = t_0
        starting_params["pi_EN"] = 0.0
        starting_params["pi_EE"] = 0.0
        fitting_method = (
            self.config["model_fit_configuration"]["PSPL_blend_piE"].get("fitting_method")
        )
        use_boundaries = (
            self.config["model_fit_configuration"]["PSPL_blend_piE"].get("boundaries", None)
        )
        results = self.fit_pspl(
            self.analyst_path + "PSPL_blend_piE",
            starting_params,
            True,
            True,
            fitting_method=fitting_method,
            use_boundaries=use_boundaries,
        )
        self.best_results["PSPL_blend_piE"] = results

        self.log.info("Evaluate PSPL+piE fit.")
        model_ok = self.evaluate_pspl(results)
        if not model_ok:
            self.log.info("Perform PSPL with parallax without blend fit.")
            fitting_method = (
                self.config["model_fit_configuration"]["PSPL_no_blend_piE"].get("fitting_method")
            )
            use_boundaries = (
                self.config["model_fit_configuration"]["PSPL_no_blend_piE"].get("boundaries", None)
            )
            results = self.fit_pspl(
                self.analyst_path + "PSPL_no_blend_piE",
                starting_params,
                True,
                False,
                fitting_method=fitting_method,
                use_boundaries=use_boundaries,
            )
            self.best_results["PSPL_noblend_par"] = results

        self.log.info("Fit Analyst:  Finished fitting.")
        self.log.debug("Best models:", self.best_results)

    def perform_finished_fit_pspl(self, t_0):
        """
        Perform fitting procedure for a finished event.
        According to the Software Requirements, the analyst
        has to perform PSPL fit with blending and with/without parallax.
        The results are appended to a dictionary and
        gathered for evaluation.
        """

        self.log.info("Fit Analyst: Starting finished event fit.")
        self.log.info("Find PSPL starting parameters.")
        # time_of_peak = analyst_tools.find_time_of_peak(self.light_curves)
        starting_params = {
            "ra": self.config["ra"],
            "dec": self.config["dec"],
            "t_0": t_0,
            "u_0": 0.1,
            "t_E": 40.0,
        }

        self.log.info("Perform PSPL with blend fit.")
        self.log.info("Perform PSPL with parallax without blend fit.")
        fitting_method = (
            self.config["model_fit_configuration"]["PSPL_blend_no_piE"].get("fitting_method")
        )
        use_boundaries = (
            self.config["model_fit_configuration"]["PSPL_blend_no_piE"].get("boundaries", None)
        )
        results = self.fit_pspl(
            self.analyst_path + "PSPL_blend_no_piE",
            starting_params,
            False,
            True,
            fitting_method=fitting_method,
            use_boundaries=use_boundaries,
        )
        self.best_results["PSPL_blend_no_piE"] = results
        self.log.info("Finished fitting PSPL with blend fit.")

        self.log.info("Perform PSPL+piE fit.")

        # starting_params['t_0'] = self.best_results['PSPL_blend_no_piE']['t0']

        starting_u_0s = [-0.1, 0.1]
        starting_pi_ens = [-0.1, 0.1]
        starting_pi_ees = [-0.1, 0.1]

        for u_0 in starting_u_0s:
            for pi_en in starting_pi_ens:
                for pi_ee in starting_pi_ees:
                    starting_params["u_0"] = u_0
                    starting_params["pi_EN"] = pi_en
                    starting_params["pi_EE"] = pi_ee
                    boundaries = {"tE": [0.0, 1000.0]}

                    signs = ""
                    for element in [u_0, pi_en, pi_ee]:
                        if element > 0.0:
                            signs += "p"
                        else:
                            signs += "m"

                    if u_0 > 0.0:
                        boundaries["u0"] = [-0.05, 2.0]
                    else:
                        boundaries["u0"] = [-2.0, 0.05]

                    if pi_en > 0.0:
                        boundaries["piEN"] = [-0.05, 2.0]
                    else:
                        boundaries["piEN"] = [-2.0, 0.05]

                    if pi_ee > 0.0:
                        boundaries["piEE"] = [-0.05, 2.0]
                    else:
                        boundaries["piEE"] = [-2.0, 0.05]

                    self.log.info(f"Fit Analyst:  Starting fitting model PSPL_blend_piE_{signs}")
                    fitting_method = (
                        self.config["model_fit_configuration"]["PSPL_blend_piE"].get("fitting_method")
                    )
                    # use_boundaries = (
                    #     self.config["model_fit_configuration"]["PSPL_blend_no_piE"].get("boundaries", None)
                    # )
                    results = self.fit_pspl(
                        self.analyst_path + "PSPL_blend_piE_" + signs,
                        starting_params,
                        True,
                        True,
                        fitting_method=fitting_method,
                        use_boundaries=boundaries,
                    )
                    self.best_results["PSPL_blend_piE_" + signs] = results
                    starting_params["t_0"] = results["t0"]

                    self.log.info(f"Fit Analyst:  Finished fitting model PSPL_blend_piE_{signs}")

    def perform_anomaly_finder(self):
        """
        Perform an anomaly finder.

        :return: boolean flag, if an anomaly was detected
        """

        anomaly_found = False

        return anomaly_found

    def evaluate_model(self):
        """
        Evaluate all found models.

        :return: return the key for the best model
        """
        best_model_name = ""

        return best_model_name

    def evaluate_pspl(self, model_params):
        """
        Check if model doesn't have negative or low blend flux.
        Lifted from mop.toolbox.fittols.test_quality_of_model_fit
        :param model_params: dict, model parameters after fitting

        :return: boolean flag if the event is okay
        """
        fit_ok = True

        blend_check = False
        if "blend_magnitude" in model_params:
            blend_check = (
                np.abs(model_params["blend_magnitude"]) < 3.0 * model_params["blend_mag_error"] ** 0.5
            )

        source_check = (
            np.abs(model_params["source_magnitude"]) < 3.0 * model_params["source_mag_error"] ** 0.5
        )

        te_check = np.abs(model_params["tE"]) < 3.0 * model_params["tE_error"] ** 0.5
        if blend_check or source_check or te_check:
            fit_ok = False

        return fit_ok

    def perform_fit(self):
        """
        Perform fitting flow.

        :return: dictionary with all found models
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
                    f"t0={params['t0']:.2f}, u0={params['u0']:.2f}, tE={params['tE']:.2f}, \n"
                    f"piEN={params['piEN']:.2f}, piEE={params['piEE']:.2f}\n"
                )
            else:
                self.log.debug(
                    f"Fit Analyst: {model:s} : \n"
                    f"t0={params['t0']:.2f}, u0={params['u0']:.2f}, tE={params['tE']:.2f}, \n"
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
                f"{'# name':<20s} : {'chi2':<7s} {'red_chi2':<7s}"
                f"{'SW':<7s} {'AD':<7s} {'KS':<7s} {'AIC':<7s} {'BIC':<7s}\n"
            )
            file.write("#--------------------------------------------------------------------------------\n")
            for model in self.best_results:
                params = self.best_results[model]
                file.write(
                    f"{model:20s} : {params['chi2']:7.2f} {params['red_chi2']:7.2f}"
                    f"{params['sw_test']:7.2f} {params['ad_test']:7.2f} {params['ks_test']:7.2f}"
                    f"{params['aic_test']:7.2f} {params['bic_test']:7.2f}\n"
                )

        return self.best_results
