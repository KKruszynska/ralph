import numpy as np

from ralph.analyst.analyst import Analyst


class LightCurveAnalyst(Analyst):
    """
    Performs light curve quality test and removes bad data entries that would interfere
    with modeling a microlensing event.
    It is a subclass of the :class:`ralph.analyst.analyst.Analyst`.
    It follows a flowchart specified here: link link link

    The Light Curve Analyst needs either a config_path or config_dict, otherwise it will not work.

    :param event_name: A name of the analyzed event.
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

    def __init__(self, event_name, analyst_path, light_curves, log, config_dict=None, config_path=None):

        super().__init__(event_name, analyst_path, config_dict=config_dict, config_path=config_path)

        self.acceptable_mag_range = None
        self.light_curves = light_curves
        self.log = log

        if config_dict is not None:
            self.add_lc_config(config_dict)
        elif "lc_analyst" in self.config:
            self.add_lc_config(self.config)
        else:
            self.log.error("LC Analyst: Error! Light Curve Analyst needs configuration parameters.")
            quit()

    def add_lc_config(self, config_dict):
        """
        Adds Light Curve Analyst configuration fields to the analyst's internal
        configuration dictionary.

        :param config_dict: A dictionary with analyst config
        :type config_dict: dict
        """

        self.log.debug("LC Analyst: Reading lc config.")
        self.acceptable_mag_range = config_dict["lc_analyst"].get("acceptable_mag_range", None)
        self.log.debug("LC Analyst: Finished reading lc config.")

    def perform_quality_check(self):
        """
        Performs a quality checks of light curves stored in the internal dictionary,
        and applies masks to invalid entries. A cleaned light curve replaces
        the old entry in the internal analyst dictionary.
        """

        self.log.info("LC Analyst: Start quality check.")
        for entry in self.light_curves:
            # extract np array with the light curve
            lc = np.array(entry["light_curve"])

            self.log.debug("LC Analyst: Masking bad data.")
            mask_duplicate = self.flag_duplicate_entries(lc)
            mask_inf_entry = self.flag_infinite_entries(lc)
            preliminary_mask = np.logical_and(mask_inf_entry, mask_duplicate)
            preliminary_lc = lc[preliminary_mask]
            self.log.debug("LC Analyst: Applying non numerical and duplicates mask.")

            mask_inv_mags = self.flag_invalid_mags(preliminary_lc)
            self.log.debug("LC Analyst: Applying bad data mask.")
            cleaned_lc = preliminary_lc[mask_inv_mags]

            mask_neg_err = self.flag_negative_errorbars(preliminary_lc)
            fin_lc = cleaned_lc[mask_neg_err]
            entry["light_curve"] = fin_lc

        self.log.info("LC Analyst: Quality check ended.")

    def flag_infinite_entries(self, light_curve):
        """
        Flags entries with non-finite values and creates a mask for finite entries only.

        :param light_curve: An array containing Julian Days, magnitudes and errors
            for the whole light curve.
        :type light_curve: numpy ndarray

        :return: A mask with entries that are only finite values.
        """

        mask_finite_mag = np.isfinite(light_curve[:, 1])
        mask_finite_err = np.isfinite(light_curve[:, 2])
        final_mask = np.logical_and(mask_finite_mag, mask_finite_err)

        return final_mask

    def flag_negative_errorbars(self, light_curve):
        """
        Flags entries with negative errors.

        :param light_curve: An array containing Julian Days, magnitudes and errors
            for the whole light curve.
        :type light_curve: numpy ndarray

        :return: A mask with entries that have only positive uncertainties.
        """

        mask_neg_err = np.where(light_curve[:, 2] > 0)

        return mask_neg_err

    def flag_invalid_mags(self, light_curve):
        """
        Flags entries outside the allowed magnitude range (`lower_limit` < mag < `upper_limit`).
        This is to clean up invalid entries flagged by the survey itself.
        Many surveys indicate an invalid entry by applying -99, 99, or similar values to invalid
        entries in the light curve.

        :param light_curve: An array containing Julian Days, magnitudes and errors
            for the whole light curve.
        :type light_curve: numpy ndarray

        :return: A mask with entries within allowed magnitude range.
        """

        custom_range = self.acceptable_mag_range
        if custom_range is not None:
            mask_inv_mag = np.where(
                (light_curve[:, 1] > custom_range["upper_limit"])
                & (light_curve[:, 1] < custom_range["lower_limit"])
            )
        else:
            mask_inv_mag = np.where((light_curve[:, 1] > -10) & (light_curve[:, 1] < 40))

        return mask_inv_mag

    def flag_duplicate_entries(self, light_curve):
        """
        Flags duplicate entries in the light curve.

        :param light_curve: An array containing Julian Days, magnitudes and errors
            for the whole light curve.
        :type light_curve: numpy ndarray

        :return: A mask with unique entries.
        """

        unique_entries, unique_index = np.unique(light_curve[:, 0], return_index=True)
        mask_unique = []
        for i in range(len(light_curve[:, 0])):
            if i in unique_index:
                mask_unique.append(True)
            else:
                mask_unique.append(False)

        return mask_unique
