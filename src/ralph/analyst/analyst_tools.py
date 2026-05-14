
import numpy as np

from astropy.table import QTable
from astropy.time import Time
from astropy.timeseries import TimeSeries, aggregate_downsample
from astropy import units as u

from ralph.fitting_support.pylima import fit_pylima


def cmd_catalogues_to_bands(catalogue):
    """
    This function provides a list of bands used to create a CMD with the requested catalogue.

    :param catalogue: str, catalogue name

    :return: list of bands
    """
    bands = None

    if "Gaia" in catalogue:
        bands = ["Gaia_G", "Gaia_BP", "Gaia_RP"]

    return bands


def get_baseline_mag(mag_source, err_source, mag_blend, err_blend, fit_package, log):
    """
    This function returns baseline magnitude based on source and blend magnitude.

    :param mag_source: source brightness in magnitudes
    :param err_source: source uncertainty in magnitudes
    :param mag_blend: blend brightness in magnitudes
    :param err_blend: blend uncertainty in magnitudes
    :param fit_package: package used for fitting
    :param log: logger instance

    :return: baseline brightness and its uncertainty in magnitudes
    """
    baseline_mag, err_baseline_mag = None, None

    if not np.isnan(mag_source) and not np.isnan(mag_blend):
        if fit_package.lower() == "pylima":
            baseline_mag, err_baseline_mag = fit_pylima.return_baseline_mag(
                mag_source, err_source, mag_blend, err_blend, log
            )
        else:
            placeholder(10)

    return [baseline_mag, err_baseline_mag]


def get_blend_mag(mag_source, err_source, mag_base, err_base, fit_package, log):
    """
    This function returns blend magnitude based on source and baseline magnitude.

    :param mag_source: source brightness in magnitudes
    :param err_source: source uncertainty in magnitudes
    :param mag_base: baseline brightness in magnitudes
    :param err_base: baseline uncertainty in magnitudes
    :param fit_package: package used for fitting
    :param log: logger instance

    :return: baseline brightness and its uncertainty in magnitudes
    """
    blend_mag, err_blend_mag = None, None

    if not np.isnan(mag_source) and not np.isnan(mag_base):
        if fit_package.lower() == "pylima":
            blend_mag, err_blend_mag = fit_pylima.return_blend_mag(
                mag_source, err_source, mag_base, err_base, log
            )
        else:
            placeholder(10)

    return [blend_mag, err_blend_mag]


def placeholder(n_max):
    """
    Placeholder function to put in parts of the code that are not complete.

    :param n_max: int, maximum number of the counter

    :return: counted number, should be equal to n_max
    """

    count = 0
    for _i in range(n_max):
        count += 1

    return count


def find_time_of_peak(light_curves, bin_size):
    """
    Find the time of peak among all the light curves.

    :param light_curves: list of light curves

    :return: time of peak in JD
    """

    time_of_peak = 0.0
    max_amplitude = 0.0
    for entry in light_curves:
        lc = np.asarray(entry["light_curve"])
        time = Time(lc[:,0], format='jd')
        mag, err = lc[:,1] * u.mag, lc[:,2] * u.mag
        lc = QTable(
            data=[time, mag, err],
            names=['time', 'mag', 'err'],
        )
        time_series = TimeSeries(lc)
        lc_binned = aggregate_downsample(
            time_series,
            time_bin_size=bin_size * u.day,
            aggregate_func=np.nanmedian
        )

        idx_max = np.nanargmin(lc_binned['mag'])
        amplitude = np.nanmax(lc_binned['mag']) - lc_binned['mag'][idx_max]
        time_max = lc_binned['time_bin_start'][idx_max]

        if max_amplitude < amplitude:
            time_of_peak, max_amplitude = time_max, amplitude

    return time_of_peak.jd


def check_ongoing_time(model_params, time_now):
    """
    Checks if based on current time and model, the event reached baseline.
    This check is passed if current time is smaller than the sum of the time
    of peak and Einstein time.

    :param model_params: dict, dictionary containing model parameters
    :param time_now: float, current time in JD

    :return: boolean flag if the event is ongoing
    """
    ongoing = False
    t_0, t_e = model_params["t0"], model_params["tE"]

    if t_0 + t_e > time_now:
        ongoing = True

    return ongoing


def check_ongoing_amplitude(threshold, aligned_data, residuals, baseline_mag):
    """
    Checks if the event is over or not, comparing baseline magnitude, magnitude
    of the last point aligned with the model and the standard deviation of the
    model residuals.

    :param threshold: float, if the amplitude is larger than threshold amount of standard deviation of
                      the light curve, then the event is considered ongoing
    :param aligned_data: numpy array, array containing photometric data aligned to a microlensing model
    :param residuals: numpy array, array containing residuals of the microlensing model
    :param baseline_mag: float, baseline magnitude of the model

    :return: boolean, is the event over and the time of the last point
    """
    ongoing = False

    # find standard deviation
    sigmas = []
    for data in residuals:
        sigmas.append(np.std(data[:, 1]))
    sigmas = np.asarray(sigmas)
    std_mag = np.sqrt(np.sum(sigmas**2))

    # Find last data point
    t_last = 0
    for data in aligned_data:
        if data[-1, 0] > t_last:
            t_last = data[-1, 0]
            if np.abs(data[-1, 1] - baseline_mag) > threshold * std_mag:
                ongoing = True

    return ongoing, t_last


def check_ongoing_magnification(threshold, model_params, time_now):
    """
    Checks if the event is ongoing based on microlensing model's magnification.

    :param threshold: float, threshold for microlensing model's magnification, if larger
                       the event is considered ongoing
    :param model_params: dict, dictionary containing microlensing model parameters
    :param time_now: current time

    :return: boolean flag if the event is still ongoing
    """
    ongoing = False
    t_0, u_0, t_e = model_params["t0"], model_params["u0"], model_params["tE"]

    tau = (time_now - t_0) / t_e
    u = np.sqrt(u_0**2 + tau**2)
    magnification = (u**2 + 2) / (u * np.sqrt(u**2 + 4))

    if magnification > threshold:
        ongoing = True

    return ongoing
