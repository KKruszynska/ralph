def cmd_catalogues_to_bands(catalogue):
    """
    Provides a list of bands used to create a CMD with the requested catalogue.

    :param catalogue: The name of the catalogue provided in the configuration.
    :type catalogue: str

    :return: list of bands
    :rtype: list
    """
    bands = None

    if "Gaia" in catalogue:
        bands = ["Gaia_G", "Gaia_BP", "Gaia_RP"]

    return bands