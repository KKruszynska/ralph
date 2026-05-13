import numpy as np

from ralph.fitting_support.pylima import fit_pylima

def get_baseline_mag(mag_source, err_source, mag_blend, err_blend, fit_package, log):
    """
    Returns baseline magnitude based on source and blend magnitude.

    :param mag_source: Source brightness in magnitudes.
    :type mag_source: float

    :param err_source: Source uncertainty in magnitudes.
    :type err_source: float

    :param mag_blend: Blend brightness in magnitudes.
    :type mag_blend: float

    :param err_blend: blend uncertainty in magnitudes.
    :type err_blend: float

    :param fit_package: Name of the package used for fitting events.
    :type fit_package: str

    :param log: A logger instance started by the Event Analyst.
    :type log: logging.Logger

    :return: Baseline brightness and its uncertainty in magnitudes.
    :rtype: [float, float]
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
    Returns blend magnitude based on source and baseline magnitude.

    :param mag_source: Source brightness in magnitudes.
    :type mag_source: float

    :param err_source: Source uncertainty in magnitudes.
    :type err_source: float

    :param mag_base: Baseline brightness in magnitudes.
    :type mag_base: float

    :param err_base: Baseline uncertainty in magnitudes.
    :type err_base: float

    :param fit_package: The name of the package used for fitting events.
    :type fit_package: str

    :param log: A logger instance started by the Event Analyst.
    :type log: logging.Logger

    :return: Baseline brightness and its uncertainty in magnitudes.
    :rtype: [float, float]
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
    It counts to the number of n_max end then ends.

    :param n_max: A maximum number of the counter.
    :type n_max: int

    :return: Counted number, equal to n_max.
    :rtype: int
    """

    count = 0
    for _i in range(n_max):
        count += 1

    return count


def find_time_of_peak(light_curves):
    """
    Finds the time of peak among all the light curves.

    :param light_curves: A list of  dictionaries containing light curves.
    :type light_curves: list

    :return: time of peak in JD
    :rtype: float
    """

    time_of_peak = 0.0
    max_amplitude = 0.0

    # first, lets bin the data
    binned_lc = []
    for entry in light_curves:
        lc = np.asarray(entry["light_curve"])

    for entry in light_curves:
        lc = np.asarray(entry["light_curve"])
        idx_max = np.argmin(lc[:, 1])
        amplitude = np.max(lc[:, 1]) - lc[idx_max, 1]
        time_max = lc[idx_max, 0]

        if max_amplitude < amplitude:
            time_of_peak, max_amplitude = time_max, amplitude

    return time_of_peak


def check_ongoing_time(model_params, time_now):
    """
    Checks if based on current time and model, the event reached baseline.
    This check is passed if current time is smaller than the sum of the time
    of peak and Einstein time.

    :param model_params: A dictionary containing model parameters.
    :type model_params: dict

    :param time_now: Julian Date of the latest data point.
    :type time_now: float

    :return: A flag, `True` if time of the latest data point is larger than the sum
        of the base point source-point lens model's time of peak and Einstein timescale,
        `False` otherwise.
    :rtype: bool
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

    :param threshold: Threshold for the amplitude; if the amplitude is larger than
        the threshold amount of standard deviation of the light curve, then the event
        is considered ongoing.
    :type threshold: float

    :param aligned_data: An array containing photometric data aligned to
        a microlensing model.
    :type aligned_data: numpy array

    :param residuals: An array containing residuals of the microlensing model.
    :type residuals: numpy array

    :param baseline_mag: The baseline magnitude of the microlensing model.
    :type baseline_mag: float

    :return: A flag of the amplitude check and the Julian Date of the latest data point.
        The flag is `True` if the amplitude at the lastest data point is above
        the threshold times standard deviation from the baseline, `False` otherwise.
    :rtype: bool, float
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

    :param threshold: A threshold for microlensing model's magnification, if larger
                       the event is considered ongoing.
    :type threshold: float

    :param model_params: A dictionary containing microlensing model parameters.
    :type model_params: dict

    :param time_now: Julian Date of the latest data point.
    :type time_now: float

    :return: A flag, `True` if the magnification of the base point source-point lens model
        at the latest data point is larger than the threshold, `False` otherwise.
    :rtype: bool
    """
    ongoing = False
    t_0, u_0, t_e = model_params["t0"], model_params["u0"], model_params["tE"]

    tau = (time_now - t_0) / t_e
    u = np.sqrt(u_0**2 + tau**2)
    magnification = (u**2 + 2) / (u * np.sqrt(u**2 + 4))

    if magnification > threshold:
        ongoing = True

    return ongoing
