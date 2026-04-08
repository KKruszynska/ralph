import numpy as np
from src.ralph.fitting_support import fit_pyLIMA


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
    :return: baseline brightness and its uncertainty in magnitudes
    """
    baseline_mag, err_baseline_mag = None, None

    if not np.isnan(mag_source) and not np.isnan(mag_blend):
        if fit_package == "pyLIMA":
            baseline_mag, err_baseline_mag = fit_pyLIMA.return_baseline_mag(mag_source, err_source,
                                                                            mag_blend, err_blend,
                                                                            log)

    return [baseline_mag, err_baseline_mag]

def get_blend_mag(mag_source, err_source, mag_base, err_base, fit_package, log):
    """
    This function returns blend magnitude based on source and baseline magnitude.

    :param mag_source: source brightness in magnitudes
    :param err_source: source uncertainty in magnitudes
    :param mag_base: baseline brightness in magnitudes
    :param err_base: baseline uncertainty in magnitudes
    :param fit_package: package used for fitting
    :return: baseline brightness and its uncertainty in magnitudes
    """
    blend_mag, err_blend_mag = None, None

    if not np.isnan(mag_source) and not np.isnan(mag_base):
        if fit_package == "pyLIMA":
            blend_mag, err_blend_mag = fit_pyLIMA.return_blend_mag(mag_source, err_source,
                                                                   mag_base, err_base,
                                                                   log)

    return [blend_mag, err_blend_mag]
