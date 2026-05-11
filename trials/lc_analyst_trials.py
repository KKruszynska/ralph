def flag_huge_errorbars(self, light_curve):
    """
    Flags entries with huge errors.

    :TODO: fill out this function

    :param light_curve: An array containing Julian Days, magnitudes and errors
        for the whole light curve.
    :type light_curve: numpy ndarray

    :return: mask containing entries that have huge uncertainty values
    """

    return 0.0