import numpy as np
from pyLIMA import event, telescopes, toolbox
from pyLIMA.fits import DE_fit, TRF_fit, stats
from pyLIMA.fits.objective_functions import photometric_residuals_in_magnitude
from pyLIMA.models import PSPL_model
from pyLIMA.outputs.pyLIMA_plots import create_telescopes_to_plot_model

from ralph.fitting_support.fitter import Fitter
from ralph.fitting_support.pylima import plots_pylima


class FitPylima(Fitter):
    """
    A class containing functions necessary to perform microlensing model fitting
    with the pyLIMA package, found here: https://github.com/ebachelet/pyLIMA
    It is a subclass of the :class ralph.src.fitting_support.fit.Fitter:.

    :param log: A logger instance initialized by the Event Analyst, to which the logs will be written.
    :type log: logging.Logger
    """

    def __init__(self, log):
        super().__init__(log)

    def setup_event(self, event_name, ra, dec, light_curves):
        """
        Set up pyLIMA Event instance.

        :param event_name: Technically a label of the event, but in fact a path to which the plot
            with best-fitting model will be saved.
        :type event_name: str

        :param ra: Right Ascension of the event
        :type ra: float, in degrees

        :param dec: Declination of the event
        :type dec: float, in degrees

        :param light_curves: A list of dictionaries with event name, light curve, survey name, filter name,
            and, if available, an ephemeris of the space observatory which was used to obtain the observations.
        :type light_curves: list

        :return: pyLIMA Event instance.
        :rtype: pyLIMA.event.Event
        """

        event_to_fit = event.Event(ra=ra, dec=dec)
        event_to_fit.name = event_name

        t_min, t_max = 10e9, 0.0
        survey_to_align = ""
        max_n_points = 0
        for entry in light_curves:

            lc = np.array(entry["light_curve"])
            survey = entry["survey"]
            band = entry["band"]
            if (t_min > np.min(lc[:, 0])) and (t_max < np.max(lc[:, 0])) and (max_n_points < len(lc[:, 0])):
                survey_to_align = survey
                max_n_points = len(lc[:, 0])
                t_min, t_max = np.min(lc[:, 0]), np.max(lc[:, 0])

            if "ephemeris" in entry and entry["ephemeris"] is not None:
                self.log.debug("Fit Analyst -- pyLIMA: Loading provided ephemeris.")
                ephemeris = entry["ephemeris"]

                spacecraft_positions = {"photometry": ephemeris}

                telescope = telescopes.Telescope(
                    name=survey + "_" + band,
                    camera_filter=band,
                    lightcurve=lc.astype(float),
                    lightcurve_names=["time", "mag", "err_mag"],
                    lightcurve_units=["JD", "mag", "mag"],
                    location="Space",
                    spacecraft_name=survey,
                    spacecraft_positions=spacecraft_positions,
                )

            else:
                telescope = telescopes.Telescope(
                    name=survey + "_" + band,
                    camera_filter=band,
                    lightcurve=lc.astype(float),
                    lightcurve_names=["time", "mag", "err_mag"],
                    lightcurve_units=["JD", "mag", "mag"],
                    location="Earth",
                )

            event_to_fit.telescopes.append(telescope)

        self.log.debug(f"Fit Analyst -- pyLIMA: Survey to align data to: {survey_to_align:s}")
        event_to_fit.find_survey(survey_to_align)
        event_to_fit.check_event()

        return event_to_fit

    def fit_pspl(
        self,
        fit_name,
        light_curves,
        starting_params,
        parallax,
        blend,
        return_norm_lc=False,
        use_boundaries=None,
        fitting_method=None,
    ):
        """
        Perform a point source-point lens model fit.

        :param fit_name: A label, but in fact a path to which the plot with
            the best-fitting model will be saved.
        :type fit_name: str

        :param light_curves: A list of dictionaries with event name, light curve, survey name, filter name,
            and, if available, an ephemeris of the space observatory which was used to obtain the observations.
        :type light_curves: list

        :param starting_params: A dictionary containing starting parameters.
        :type starting_params: dict

        :param parallax: If `True` microlensing parallax effect will be included in the model,
            if `False` it will not.
        :type parallax: bool

        :param blend: If `True` blending will be fitted for this event, if `False`, the model will assume
            that all light is coming from the source.
        :type blend: bool

        :param return_norm_lc: If `True`, this method will return a light curve and residuals aligned to
            the best-fitting model it found.
        :type return_norm_lc: bool, optional

        :param use_boundaries: A dictionary containing upper and lower limits for specific
            model parameters, defined by the User.
        :type use_boundaries: dict, optional

        :param fitting_method: A label of the type of fitting method used in pyLIMA.
        :type fitting_method: str, optional

        :return: A dictionary with the parameters of the best-fitting model, and, if available, a list with
            a light curve aligned to it and its residuals.
        :rtype: list
        """

        # Setup event
        event_name = fit_name
        ra, dec = float(starting_params["ra"]), float(starting_params["dec"])
        event = self.setup_event(event_name, ra, dec, light_curves)

        blend_param = "ftotal" if blend else "noblend"

        if parallax:
            self.log.info("Fit Analyst -- pyLIMA: Fitting with microlensing parallax.")
            pspl = PSPL_model.PSPLmodel(
                event, parallax=["Full", int(starting_params["t0"])], blend_flux_parameter=blend_param
            )
        else:
            self.log.info("Fit Analyst -- pyLIMA: Fitting without microlensing parallax.")
            pspl = PSPL_model.PSPLmodel(event, parallax=["None", 0.0], blend_flux_parameter=blend_param)

        if fitting_method is not None:
            self.log.info(f"Fit Analyst -- pyLIMA: Fitting method: {fitting_method}.")
            if fitting_method == "DE":
                fit_event = DE_fit.DEfit(pspl, loss_function="soft_l1")
            elif fitting_method == "TRF":
                fit_event = TRF_fit.TRFfit(pspl, loss_function="soft_l1")
        else:
            self.log.info("Fit Analyst -- pyLIMA: Using default fitting method (TRF).")
            fit_event = TRF_fit.TRFfit(pspl, loss_function="soft_l1")

        # Use boundries like in mop.toolbox.fittools
        if use_boundaries is None:
            self.log.info("Fit Analyst -- pyLIMA: Using boundaries default for ralph.")
            delta_t0 = 50.0
            default_t0_lower = fit_event.fit_parameters["t0"][1][0]
            default_t0_upper = fit_event.fit_parameters["t0"][1][1]
            fit_event.fit_parameters["t0"][1] = [default_t0_lower, default_t0_upper + delta_t0]
            fit_event.fit_parameters["tE"][1] = [0.0, 1000.0]
            fit_event.fit_parameters["u0"][1] = [0.0, 2.0]
            if parallax:
                fit_event.fit_parameters["piEN"][1] = [-2.0, 2.0]
                fit_event.fit_parameters["piEE"][1] = [-2.0, 2.0]
        else:
            self.log.info("Fit Analyst -- pyLIMA: Using boundaries passed by the User.")
            for key in use_boundaries:

                fit_event.fit_parameters[key][1] = [use_boundaries[key][0], use_boundaries[key][1]]

        self.log.info("Fit Analyst -- pyLIMA: Staring fit.")
        fit_event.fit()
        self.log.info("Fit Analyst -- pyLIMA: Fitting finished")

        # This will have to be modified to be compatible with MOP
        self.log.debug("Fit Analyst -- pyLIMA: Convert model parameters to dictionary.")
        model_parameters = self.gather_parameters(event, fit_event, fitting_method=fitting_method)

        # Produce fit outputs here
        plots_pylima.plot_pylima(event, fit_event, self.log)

        if return_norm_lc:
            norm_lc, residuals = self.get_aligned_data(pspl, fit_event.fit_results["best_model"])
            return model_parameters, norm_lc, residuals

        return model_parameters

    def gather_parameters(self, event, model_fit, fitting_method=None):
        """
        Gathers parameters into a dictionary, for easier handling.
        Like in mop.toolbox.fittools, but edited to accommodate wider usage in `ralph`.

        :param event: A pyLIMA event instance.
        :type event: pyLIMA.event.Event

        :param model_fit: A pyLIMA model instance.
        :type model_fit: pyLIMA.model

        :param fitting_method: A label of the type of fitting method used by pyLIMA.
        :type fitting_method: str, optional

        :return: A dictionary with best-fitting parameters of the model, their uncertianities,
            and several statistical parameters to measure the quality of the model.
        :rtype: dict
        """

        if fitting_method is not None:
            if fitting_method == "DE":
                param_keys = list(model_fit.priors_parameters.keys())
            elif fitting_method == "TRF":
                param_keys = list(model_fit.fit_parameters.keys())
        else:
            param_keys = list(model_fit.fit_parameters.keys())

        model_params = {
            "t0_par": model_fit.model.parallax_model[1],
        }

        if fitting_method is not None and fitting_method == "DE":
            samples = model_fit.fit_results["DE_population"]
            percentiles = np.percentile(samples, [16, 50, 84], axis=0)

        for i, key in enumerate(param_keys):
            ndp = 3 if key in ["t0", "tE"] else 5

            if fitting_method == "DE":
                median = percentiles[1][i]
                err_pl = percentiles[2][i] - percentiles[1][i]
                err_mn = percentiles[1][i] - percentiles[0][i]
                model_params[key] = np.around(median, ndp)
                model_params[key + "_error"] = np.around(np.sqrt(err_pl**2 + err_mn**2), ndp)

                # Save fluxes transformed to magnitudes
                if any(x in key for x in ["fsource", "fblend", "ftotal"]):
                    model_params[key + "_mag"] = np.around(
                        toolbox.brightness_transformation.flux_to_magnitude(median), 3
                    )
                    model_params[key + "_mag_error"] = np.around(
                        toolbox.brightness_transformation.error_flux_to_error_magnitude(
                            np.sqrt(np.sqrt(err_pl**2 + err_mn**2)),
                            median,
                        ),
                        3,
                    )
            else:
                model_params[key] = np.around(model_fit.fit_results["best_model"][i], ndp)
                model_params[key + "_error"] = np.around(
                    np.sqrt(model_fit.fit_results["covariance_matrix"][i, i]), ndp
                )

                # Save fluxes transformed to magnitudes
                if any(x in key for x in ["fsource", "fblend", "ftotal"]):
                    model_params[key + "_mag"] = np.around(
                        toolbox.brightness_transformation.flux_to_magnitude(
                            model_fit.fit_results["best_model"][i]
                        ),
                        3,
                    )
                    model_params[key + "_mag_error"] = np.around(
                        toolbox.brightness_transformation.error_flux_to_error_magnitude(
                            np.sqrt(model_fit.fit_results["covariance_matrix"][i, i]),
                            model_fit.fit_results["best_model"][i],
                        ),
                        3,
                    )

        # Reporting actual chi2 instead value of the loss function
        chi2, pylima_parameters = model_fit.model_chi2(model_fit.fit_results["best_model"])
        model_params["chi2"] = np.around(chi2, 3)

        ndata = 0
        tel_0 = ""
        for i, tel in enumerate(event.telescopes):
            ndata += len(tel.lightcurve["mag"])

            if i == 0:
                tel_0 = tel.name

            if f"fblend_{tel.name}" in model_params:
                return_baseline_mag
                model_params["ftotal_" + tel.name] = (
                    model_params["fsource_" + tel.name] + model_params["fblend_" + tel.name]
                )
                model_params["ftotal_" + tel.name + "_error"] = np.sqrt(
                    model_params["fsource_" + tel.name + "_error"] ** 2
                    + model_params["fblend_" + tel.name + "_error"] ** 2
                )

                model_params["ftotal_" + tel.name + "_mag"] = np.around(
                    toolbox.brightness_transformation.flux_to_magnitude(model_params["ftotal_" + tel.name]), 3
                )

                model_params["ftotal_" + tel.name + "_mag_error"] = np.around(
                    toolbox.brightness_transformation.error_flux_to_error_magnitude(
                        model_params["ftotal_" + tel.name + "_error"], model_params["ftotal_" + tel.name]
                    ),
                    3,
                )

            elif f"ftotal_{tel.name}" in model_params:
                model_params["fblend_" + tel.name] = (
                    model_params["ftotal_" + tel.name] - model_params["fsource_" + tel.name]
                )

                model_params["fblend_" + tel.name + "_error"] = np.sqrt(
                    model_params["fsource_" + tel.name + "_error"] ** 2
                    + model_params["ftotal_" + tel.name + "_error"] ** 2
                )

                model_params["fblend_" + tel.name + "_mag"] = np.around(
                    toolbox.brightness_transformation.flux_to_magnitude(model_params["fblend_" + tel.name]), 3
                )

                model_params["fblend_" + tel.name + "_mag_error"] = np.around(
                    toolbox.brightness_transformation.error_flux_to_error_magnitude(
                        model_params["fblend_" + tel.name + "_error"], model_params["fblend_" + tel.name]
                    ),
                    3,
                )

            # Source magnitude for base telescope, for MOP
            model_params["source_magnitude"] = model_params["fsource_" + tel_0 + "_mag"]
            model_params["source_mag_error"] = model_params["fsource_" + tel_0 + "_mag_error"]
            if f"fblend_{tel_0}_mag" in model_params:
                model_params["blend_magnitude"] = model_params["fblend_" + tel_0 + "_mag"]
                model_params["blend_mag_error"] = model_params["fblend_" + tel_0 + "_mag_error"]
            if f"ftotal_{tel_0}_mag" in model_params:
                model_params["baseline_magnitude"] = model_params["ftotal_" + tel_0 + "_mag"]
                model_params["baseline_mag_error"] = model_params["ftotal_" + tel_0 + "_mag_error"]
            else:
                model_params["baseline_magnitude"] = model_params["source_magnitude"]
                model_params["baseline_mag_error"] = model_params["source_mag_error"]

        # Calculate the reduced chi2
        model_params["red_chi2"] = np.around(model_params["chi2"] / float(ndata - len(param_keys)), 3)

        # Calculate fit statistics
        try:
            n_parameters = len(param_keys)

            res = model_fit.model_residuals(model_fit.fit_results["best_model"])
            sw_test = stats.normal_Shapiro_Wilk(
                np.ravel(res[0]["photometry"][0]) / np.ravel(res[1]["photometry"][0])
            )
            model_params["sw_test"] = np.around(sw_test[0], 3)

            ad_test = stats.normal_Anderson_Darling(
                np.ravel(res[0]["photometry"][0]) / np.ravel(res[1]["photometry"][0])
            )
            model_params["ad_test"] = np.around(ad_test[0], 3)

            ks_test = stats.normal_Kolmogorov_Smirnov(
                np.ravel(res[0]["photometry"][0]) / np.ravel(res[1]["photometry"][0])
            )
            model_params["ks_test"] = np.around(ks_test[0], 3)

            aic_test = stats.Akaike_Information_Criterion(model_params["chi2"], n_parameters)
            model_params["aic_test"] = np.around(aic_test, 3)

            bic_test = stats.Bayesian_Information_Criterion(model_params["chi2"], ndata, n_parameters)
            model_params["bic_test"] = np.around(bic_test, 3)

        except Exception as err:
            self.log.error(f"Fit Analyst: {err}, {type(err)}")

            model_params["sw_test"] = np.nan
            model_params["ad_test"] = np.nan
            model_params["ks_test"] = np.nan
            model_params["aic_test"] = np.nan
            model_params["bic_test"] = np.nan

        return model_params

    def get_aligned_data(self, model, parameters):
        """
        Returns light curve aligned to the best fitting model, and its residuals.
        Taken from pyLIMA.outputs.pyLIMA_plots

        :param model: A pyLIMA model instance.
        :type model: pyLIMA.model

        :param parameters: A dictionary with parameters of a pyLIMA model.
        :type parameters: dict

        :return: A list with numpy arrays containing light curve data aligned to a model and its residuals.
        :rtype: list
        """

        pylima_parameters = model.compute_pyLIMA_parameters(parameters)

        # plot aligned data
        list_of_telescopes = create_telescopes_to_plot_model(model, pylima_parameters)

        ref_names = []
        ref_locations = []
        ref_magnification = []
        ref_fluxes = []

        for ref_tel in list_of_telescopes:
            model_magnification = model.model_magnification(ref_tel, pylima_parameters)

            model.derive_telescope_flux(ref_tel, pylima_parameters, model_magnification)

            f_source = pylima_parameters["fsource_" + ref_tel.name]
            f_blend = pylima_parameters["fblend_" + ref_tel.name]

            ref_names.append(ref_tel.name)
            ref_locations.append(ref_tel.location)
            ref_magnification.append(model_magnification)
            ref_fluxes.append([f_source, f_blend])

        aligned_data = []
        residuals = []
        # reference_source, reference_blend = 0., 0.
        for ind, tel in enumerate(model.event.telescopes):
            if tel.lightcurve["flux"] is not None:
                ref_index = 0
                if tel.location == "Earth":
                    ref_index = np.where(np.array(ref_locations) == "Earth")[0][0]
                else:
                    ref_index = np.where(np.array(ref_names) == tel.name)[0][0]

                residues_in_mag = photometric_residuals_in_magnitude(tel, model, pylima_parameters)
                if ind == 0:
                    reference_source = ref_fluxes[ind][0]
                    reference_blend = ref_fluxes[ind][1]

                # time_mask = [False for i in range(len(ref_magnification[ref_index]))]
                time_mask = []
                for time in tel.lightcurve["time"].value:
                    time_index = np.where(list_of_telescopes[ref_index].lightcurve["time"].value == time)[0][
                        0
                    ]
                    time_mask.append(time_index)

                model_flux = reference_source * ref_magnification[ref_index][time_mask] + reference_blend
                magnitude = toolbox.brightness_transformation.flux_to_magnitude(model_flux)

                aligned_magnitude = np.array(
                    [
                        tel.lightcurve["time"].value,
                        magnitude + residues_in_mag,
                        tel.lightcurve["err_mag"].value,
                    ]
                )
                res_magnitude = np.array(
                    [tel.lightcurve["time"].value, residues_in_mag, tel.lightcurve["err_mag"].value]
                )

                aligned_data.append(aligned_magnitude.T)
                residuals.append(res_magnitude.T)

        return aligned_data, residuals


def return_baseline_mag(mag_source, err_mag_source, mag_blend, err_mag_blend, log):
    """
    Returns baseline magnitude based on source and blend magnitude.

    :param mag_source: The source brightness in magnitudes.
    :type mag_source: float

    :param err_mag_source: The source uncertainty in magnitudes.
    :type err_mag_source: float

    :param mag_blend: The blend brightness in magnitudes.
    :type mag_blend: float

    :param err_mag_blend: The blend uncertainty in magnitudes.
    :type err_mag_blend: float

    :param log: A log instance started by the Event Analyst.
    :type log: logging.Logger

    :return: Baseline brightness and its uncertainty in magnitudes.
    :rtype: tuple, (float, float)
    """
    base_mag, err_base_mag = None, None

    flux_source = toolbox.brightness_transformation.magnitude_to_flux(mag_source)
    err_fs = toolbox.brightness_transformation.error_magnitude_to_error_flux(err_mag_source, flux_source)
    flux_blend = toolbox.brightness_transformation.magnitude_to_flux(mag_blend)
    err_fb = toolbox.brightness_transformation.error_magnitude_to_error_flux(err_mag_blend, flux_blend)

    base_flux = flux_source + flux_blend
    err_f_base = np.sqrt(err_fs**2 + err_fb**2)

    try:
        base_mag = toolbox.brightness_transformation.flux_to_magnitude(base_flux)
        err_base_mag = toolbox.brightness_transformation.error_flux_to_error_magnitude(err_f_base, base_flux)
    except Exception as err:
        log.error(f"Fit Analyst -- pyLIMA: {err}, {type(err)}")

    return base_mag, err_base_mag


def return_blend_mag(mag_source, err_mag_source, mag_base, err_mag_base, log):
    """
    Returns blend magnitude based on source and baseline magnitude.

    :param mag_source: The source brightness in magnitudes.
    :type mag_source: float

    :param err_mag_source: The source uncertainty in magnitudes.
    :type err_mag_source: float

    :param mag_base: The baseline brightness in magnitudes.
    :type mag_base: float

    :param err_mag_base: The baseline uncertainty in magnitudes.
    :type err_mag_base: float

    :param log: A log instance started by the Event Analyst.
    :type log: logging.Logger

    :return: Blend brightness and its uncertainty in magnitudes
    :rtype: tuple, (float, float)
    """
    blend_mag, err_blend_mag = None, None

    flux_source = toolbox.brightness_transformation.magnitude_to_flux(mag_source)
    err_fs = toolbox.brightness_transformation.error_magnitude_to_error_flux(err_mag_source, flux_source)
    flux_baseline = toolbox.brightness_transformation.magnitude_to_flux(mag_base)
    err_fbase = toolbox.brightness_transformation.error_magnitude_to_error_flux(err_mag_base, flux_baseline)

    blend_flux = flux_baseline - flux_source
    err_f_blend = np.sqrt(err_fs**2 + err_fbase**2)

    try:
        blend_mag = toolbox.brightness_transformation.flux_to_magnitude(blend_flux)
        err_blend_mag = toolbox.brightness_transformation.error_flux_to_error_magnitude(
            err_f_blend, blend_flux
        )
    except Exception as err:
        log.error(f"Fit Analyst -- pyLIMA: {err}, {type(err)}")

    return blend_mag, err_blend_mag
