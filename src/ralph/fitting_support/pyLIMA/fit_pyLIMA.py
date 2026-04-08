import logging

import numpy as np

from pyLIMA import event
from pyLIMA import telescopes

from pyLIMA.parallax import JPL_ephemerides

from pyLIMA import toolbox
from pyLIMA.outputs.pyLIMA_plots import create_telescopes_to_plot_model
from pyLIMA.fits.objective_functions import photometric_residuals_in_magnitude

from pyLIMA.fits import TRF_fit
from pyLIMA.fits import DE_fit

from pyLIMA.fits import stats

from pyLIMA.models import PSPL_model

from MFPipeline.fitting_support.fitter import Fitter
from MFPipeline.fitting_support.pyLIMA import plots_pyLIMA



class fitPyLIMA(Fitter):
    '''
    Class with pyLIMA fitter.

    :param log: logger instance to which the logs will be written
    '''
    def __init__(self, log):
        super().__init__(log)

    def setup_event (self, event_name, ra, dec, light_curves):
        '''
        Set up pyLIMA event instance.

        :param event_name: name of the event
        :param ra: Right Ascention of the event
        :param dec: declination of the event
        :param light_curves: list, list of lists with event name, light curve, survey name and filter name.

        :return: pyLIMA event instance
        '''

        event_to_fit = event.Event(ra=ra, dec=dec)
        event_to_fit.name = event_name

        t_min, t_max = 10e9, 0.
        survey_to_align = ""
        max_n_points = 0
        for entry in light_curves:
            lc = np.array(entry["lc"])
            survey = entry["survey"]
            band = entry["band"]
            if ((t_min > np.min(lc[:,0])) and
                (t_max < np.max(lc[:,0])) and
                (max_n_points < len(lc[:,0]))
            ):
                survey_to_align = survey
                max_n_points = len(lc[:,0])
                t_min, t_max = np.min(lc[:,0]), np.max(lc[:,0])

            if "Gaia" in survey:
                # get spacecraft positions
                ephemeris = JPL_ephemerides.horizons_API('Gaia', lc[:,0], observatory='Geocentric')[1]
                spacecraft_positions = {
                    "photometry": ephemeris
                }
                telescope = telescopes.Telescope(
                    name=survey+"_"+band,
                    camera_filter=band,
                    lightcurve=lc.astype(float),
                    lightcurve_names=["time", "mag", "err_mag"],
                    lightcurve_units=["JD", "mag", "mag"],
                    location = "Space",
                    spacecraft_name = "Gaia",
                    spacecraft_positions = spacecraft_positions
                )
            else:
                telescope = telescopes.Telescope(
                    name=survey+"_"+band,
                    camera_filter=band,
                    lightcurve=lc.astype(float),
                    lightcurve_names=['time','mag','err_mag'],
                    lightcurve_units=['JD','mag','mag'],
                    location="Earth",
                    )

            event_to_fit.telescopes.append(telescope)

        # print(survey_to_align)
        self.log.debug("Survey to align data to: %s", survey_to_align)
        event_to_fit.find_survey(survey_to_align)
        event_to_fit.check_event()

        return event_to_fit

    def fit_PSPL(self, fit_name, light_curves, starting_params, parallax, blend,
                 return_norm_lc=False,
                 use_boundaries=None,
                 ):
        '''
        Perform a PSPL fit using the selected fit method.

        todo: Test which method is better. TRF or DE?

        :param fit_name: str, label of the fit, used to save plots
        :param light_curves: list, list of lists with event name, light curve, survey name and filter name.
        :param starting_params: dict, dictionary containing starting parameters
        :param parallax: boolean, fit with parallax?
        :param blend: boolean, fit with blending?
        :param return_norm_lc: boolean, optional, return light curve data aligned to the model?
        :param use_boundaries: dict, dictionary containing boundaries defined by the User

        :return: list with results
        '''

        # Setup event
        event_name = fit_name
        ra, dec = float(starting_params["ra"]), float(starting_params["dec"])
        event = self.setup_event(event_name, ra, dec, light_curves)

        blend_param = ""
        if blend:
            blend_param = "ftotal"
        else:
            blend_param = "noblend"

        if parallax:
            self.log.info("Fitting with microlensing parallax.")
            pspl = PSPL_model.PSPLmodel(event, parallax=["Full", int(starting_params["t_0"])],
                                        blend_flux_parameter=blend_param)
        else:
            self.log.info("Fitting without microlensing parallax.")
            pspl = PSPL_model.PSPLmodel(event, parallax=["None", 0.], blend_flux_parameter=blend_param)

        fit_event = TRF_fit.TRFfit(pspl, loss_function="soft_l1")
        # fit_event = DE_fit.DEfit(pspl)

        # Use boundries like in mop.toolbox.fittools
        if use_boundaries is None:
            self.log.info("Using boundaries default for MFPipeline.")
            delta_t0 = 50.
            default_t0_lower = fit_event.fit_parameters["t0"][1][0]
            default_t0_upper = fit_event.fit_parameters["t0"][1][1]
            fit_event.fit_parameters["t0"][1] = [default_t0_lower, default_t0_upper + delta_t0]
            fit_event.fit_parameters["tE"][1] = [0., 3000.]
            fit_event.fit_parameters["u0"][1] = [-2.0, 2.0]
            if parallax:
                fit_event.fit_parameters["piEN"][1] = [-2.0, 2.0]
                fit_event.fit_parameters["piEE"][1] = [-2.0, 2.0]
        else:
            self.log.info("Using boundaries passed by the User.")
            # t_0 stays the same
            delta_t0 = 10.
            default_t0_lower = fit_event.fit_parameters["t0"][1][0]
            default_t0_upper = fit_event.fit_parameters["t0"][1][1]
            fit_event.fit_parameters["t0"][1] = [default_t0_lower, default_t0_upper + delta_t0]
            # t_E, u_0 and pi_E params passed by user
            fit_event.fit_parameters["tE"][1] = [use_boundaries["tE_lower"], use_boundaries["tE_upper"]]
            fit_event.fit_parameters["u0"][1] = [use_boundaries["u0_lower"], use_boundaries["u0_upper"]]
            if parallax:
                fit_event.fit_parameters["piEN"][1] = [use_boundaries["piEN_lower"], use_boundaries["piEN_upper"]]
                fit_event.fit_parameters["piEE"][1] = [use_boundaries["piEE_lower"], use_boundaries["piEE_upper"]]

        self.log.info("Staring fit.")
        fit_event.fit()
        self.log.info("Fitting finished")

        # This will have to be modified to be compatible with MOP
        self.log.debug("Convert model parameters to dictionary.")
        model_parameters = self.gather_parameters(event, fit_event)

        # Produce fit outputs here
        plots_pyLIMA.plot_pyLIMA(event, fit_event, self.log)
        # fit_event.fit_outputs(bokeh_plot=True)

        if return_norm_lc:
            norm_lc, residuals = self.get_aligned_data(pspl, fit_event.fit_results['best_model'])
            return model_parameters, norm_lc, residuals

        return model_parameters

    def gather_parameters(self, event, model_fit):
        '''
        Gathers parameters into a dictionary, for easier handling.
        Like in mop.toolbox.fittools, but edited to accommodate wider usage
        in Microlensing Fitting Pipeline.

        :return: dictionary with all the parameters coming from the model.
        '''

        param_keys = list(model_fit.fit_parameters.keys())

        model_params = {}

        model_params["t0_par"] = model_fit.model.parallax_model[1]

        for i, key in enumerate(param_keys):
            if key in ["t0", "tE"]:
                ndp = 3
            else:
                ndp = 5
            model_params[key] = np.around(model_fit.fit_results["best_model"][i], ndp)
            model_params[key + "_error"] = np.around(np.sqrt(model_fit.fit_results["covariance_matrix"][i, i]), ndp)

            # Save fluxes transformed to magnitudes
            if any(x in key for x in ["fsource", "fblend", "ftotal"]):
                model_params[key + "_mag"] = np.around(toolbox.brightness_transformation.flux_to_magnitude(
                    model_fit.fit_results["best_model"][i]), 3)
                model_params[key + "_mag_error"] = np.around(
                    toolbox.brightness_transformation.error_flux_to_error_magnitude(
                        np.sqrt(model_fit.fit_results["covariance_matrix"][i, i]),
                        model_fit.fit_results["best_model"][i],
                        ),
                    3)
            # if "fblend" in key:
            #     model_params[key + "_mag"] = np.around(toolbox.brightness_transformation.flux_to_magnitude(
            #         model_fit.fit_results["best_model"][i]), 3)
            #     model_params[key + "_mag_error"] = np.around(
            #         toolbox.brightness_transformation.error_flux_to_error_magnitude(
            #             model_fit.fit_results["best_model"][i],
            #             np.sqrt(model_fit.fit_results["covariance_matrix"][i, i])),
            #         3)
            # if "ftotal" in key:
            #     model_params[key + "_mag"] = np.around(toolbox.brightness_transformation.flux_to_magnitude(
            #         model_fit.fit_results["best_model"][i]), 3)
            #     model_params[key + "_mag_error"] = np.around(
            #         toolbox.brightness_transformation.error_flux_to_error_magnitude(
            #             model_fit.fit_results["best_model"][i],
            #             np.sqrt(model_fit.fit_results["covariance_matrix"][i, i])),
            #         3)

        # model_params['chi2'] = np.around(model_fit.fit_results["best_model"][-1], 3)
        # Reporting actual chi2 instead value of the loss function
        (chi2, pyLIMA_parameters) = model_fit.model_chi2(model_fit.fit_results["best_model"])
        model_params["chi2"] = np.around(chi2, 3)

        # Calculate the reduced chi2
        ndata = 0
        tel_0 = ''
        for i, tel in enumerate(event.telescopes):
            if(i == 0):
                tel_0 = tel.name
            ndata += len(tel.lightcurve["mag"])
        model_params["red_chi2"] = np.around(model_params["chi2"] / float(ndata - len(param_keys)), 3)

        key_map = {
            "fsource_"+tel_0: "source_magnitude",
            "fblend_"+tel_0: "blend_magnitude"
        }

        flux_index = []
        for pylima_key, mop_key in key_map.items():
            try:
                idx = param_keys.index(pylima_key)
                model_params[mop_key] = np.around(toolbox.brightness_transformation.flux_to_magnitude(
                    model_fit.fit_results["best_model"][idx]), 3)
                flux_index.append(idx)
            except ValueError:
                model_params[mop_key] = np.nan

        # Retrieve the flux uncertainties and convert to magnitudes
        model_params["source_mag_error"] = np.around(
            toolbox.brightness_transformation.error_flux_to_error_magnitude(
                model_params["fsource_"+tel_0+"_error"], model_params["fsource_"+tel_0]),3)

        if "fblend_"+tel_0 in model_params.keys():
            model_params["blend_mag_error"] = np.around(
                toolbox.brightness_transformation.error_flux_to_error_magnitude(
                 model_params["fblend_"+tel_0+"_error"], model_params["fblend_"+tel_0]),3)
        else:
            model_params["blend_mag_error"] = np.nan

        # If the model fitted contains valid entries for both source and blend flux,
        # use these to calculate the baseline magnitude.  Otherwise, use the source magnitude
        if "ftotal_"+tel_0 in model_params:
            unlensed_flux = model_params["ftotal_"+tel_0]
            unlensed_flux_error = model_params["ftotal_"+tel_0+"_error"]
            model_params["baseline_magnitude"] = np.around(
                toolbox.brightness_transformation.flux_to_magnitude(unlensed_flux), 3
                )
            model_params["baseline_mag_error"] = np.around(
                toolbox.brightness_transformation.error_flux_to_error_magnitude(unlensed_flux_error, unlensed_flux),
                3
            )
        elif not np.isnan(model_params["source_magnitude"]) \
                and not np.isnan(model_params["blend_magnitude"]):
            unlensed_flux = model_fit.fit_results["best_model"][flux_index[0]] \
                            + model_fit.fit_results["best_model"][flux_index[1]]
            unlensed_flux_error = np.sqrt(
                (model_params["fsource_"+tel_0+"_error"] ** 2 + model_params["fblend_"+tel_0+"_error"] ** 2)
                + (model_params["fsource_"+tel_0+"_error"] * model_params["fblend_"+tel_0+"_error"])
            )
            model_params["baseline_magnitude"] = np.around(toolbox.brightness_transformation.flux_to_magnitude(unlensed_flux), 3)
            model_params["baseline_mag_error"] = np.around(
                toolbox.brightness_transformation.error_flux_to_error_magnitude(unlensed_flux_error, unlensed_flux),
                3)
        else:
            model_params["baseline_magnitude"] = model_params["source_magnitude"]
            model_params["baseline_mag_error"] = model_params["source_mag_error"]

        model_params["fit_covariance"] = model_fit.fit_results["covariance_matrix"].tolist()

        model_params["fit_parameters"] = model_fit.fit_parameters

        # Calculate fit statistics
        try:
            n_parameters = len(param_keys)

            res = model_fit.model_residuals(model_fit.fit_results["best_model"])
            sw_test = stats.normal_Shapiro_Wilk(
                (np.ravel(res[0]["photometry"][0]) / np.ravel(res[1]["photometry"][0]))
            )
            model_params["sw_test"] = np.around(sw_test[0], 3)

            ad_test = stats.normal_Anderson_Darling(
                (np.ravel(res[0]["photometry"][0]) / np.ravel(res[1]["photometry"][0]))
            )
            model_params["ad_test"] = np.around(ad_test[0], 3)

            ks_test = stats.normal_Kolmogorov_Smirnov(
                (np.ravel(res[0]["photometry"][0]) / np.ravel(res[1]["photometry"][0]))
            )
            model_params["ks_test"] = np.around(ks_test[0], 3)

            aic_test = stats.Akaike_Information_Criterion(model_params["chi2"], n_parameters)
            model_params["aic_test"] = np.around(aic_test, 3)

            bic_test = stats.Bayesian_Information_Criterion(model_params["chi2"],
                                                            ndata, n_parameters)
            model_params["bic_test"] = np.around(bic_test, 3)

        except:
            model_params["sw_test"] = np.nan
            model_params["ad_test"] = np.nan
            model_params["ks_test"] = np.nan
            model_params["aic_test"] = np.nan
            model_params["bic_test"] = np.nan

        return model_params

    def get_aligned_data(self, model, parameters):
        '''
        Taken from pyLIMA.outputs.pyLIMA_plots

        :return: list with arrays containing aligned data
        '''

        pyLIMA_parameters = model.compute_pyLIMA_parameters(parameters)

        # plot aligned data
        index = 0

        list_of_telescopes = create_telescopes_to_plot_model(model,
                                                             pyLIMA_parameters
                                                             )

        ref_names = []
        ref_locations = []
        ref_magnification = []
        ref_fluxes = []

        for ref_tel in list_of_telescopes:
            model_magnification = model.model_magnification(ref_tel, pyLIMA_parameters)

            model.derive_telescope_flux(ref_tel, pyLIMA_parameters, model_magnification)

            f_source = pyLIMA_parameters["fsource_" + ref_tel.name]
            f_blend = pyLIMA_parameters["fblend_" + ref_tel.name]

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

                residues_in_mag = photometric_residuals_in_magnitude(tel, model, pyLIMA_parameters)
                if ind == 0:
                    reference_source = ref_fluxes[ind][0]
                    reference_blend = ref_fluxes[ind][1]

                # time_mask = [False for i in range(len(ref_magnification[ref_index]))]
                time_mask = []
                for time in tel.lightcurve["time"].value:
                    time_index = np.where(list_of_telescopes[ref_index].lightcurve["time"].value == time)[0][0]
                    time_mask.append(time_index)

                model_flux = reference_source * ref_magnification[ref_index][
                    time_mask] + reference_blend
                magnitude = toolbox.brightness_transformation.flux_to_magnitude(model_flux)

                aligned_magnitude = np.array([tel.lightcurve["time"].value,
                                             magnitude + residues_in_mag,
                                             tel.lightcurve["err_mag"].value
                                             ])
                res_magnitude = np.array([tel.lightcurve["time"].value,
                                             residues_in_mag,
                                             tel.lightcurve["err_mag"].value
                                             ])

                aligned_data.append(aligned_magnitude.T)
                residuals.append(res_magnitude.T)

        return aligned_data, residuals


def return_baseline_mag(mag_source, err_mag_source, mag_blend, err_mag_blend, log):
    """
    This function returns baseline magnitude based on source and blend magnitude.

    :param mag_source: source brightness in magnitudes
    :param err_mag_source: source uncertainty in magnitudes
    :param mag_blend: blend brightness in magnitudes
    :param err_mag_blend: source uncertainty in magnitudes
    :param fit_package: package used for fitting
    :return: baseline brightness and its uncertainty in magnitudes
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
        log.error(f"CMD Analyst: %s, %s" % (err, type(err)))

    return base_mag, err_base_mag


def return_blend_mag(mag_source, err_mag_source, mag_base, err_mag_base, log):
    """
    This function returns blend magnitude based on source and baseline magnitude.

    :param mag_source: source brightness in magnitudes
    :param err_mag_source: source uncertainty in magnitudes
    :param mag_base: baseline brightness in magnitudes
    :param err_mag_base: baseline uncertainty in magnitudes
    :return: blend brightness and its uncertainty in magnitudes
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
        err_blend_mag = toolbox.brightness_transformation.error_flux_to_error_magnitude(err_f_blend, blend_flux)
    except Exception as err:
        log.error(f"CMD Analyst: %s, %s" % (err, type(err)))

    return blend_mag, err_blend_mag

