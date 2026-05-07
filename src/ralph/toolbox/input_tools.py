import numpy as np


def load_light_curve_from_path(path):
    """
    Utility function to load light curve data from file on disk.

    :param path: path to light curve file
    :return: light curve data in numpy array
    """

    data = np.genfromtxt(path, unpack=True)
    data = data.T
    return data


def load_ephemeris_from_path(path, skip_header=0, skip_footer=0, usecols=None):
    """
    Utility function to load ephemeris data from file on disk.

    :param path: path to ephemeris file on disk
    :param skip_header: skip first line of ephemeris file
    :param skip_footer: skip last line of ephemeris file
    :param usecols: use specified column

    :return: ephemeris data in numpy array
    """

    ephemeris = np.genfromtxt(
        path,
        skip_header=skip_header,
        skip_footer=skip_footer,
        unpack=True,
        usecols=usecols,
    )
    ephemeris = ephemeris.T

    return ephemeris
