import numpy as np

import json
import os

from microlensing_ralph.analyst.analyst import BaseAnalyst
from microlensing_ralph.analyst.analyst_tools import hampel_filter, vet_outliers
from microlensing_ralph.toolbox.output_tools import plot_outlier_results


class LightCurveAnalyst(BaseAnalyst):
    """
    Performs light curve quality test and removes bad data entries that would interfere
    with modeling a microlensing event.
    It is a subclass of the :class:`microlensing_ralph.analyst.analyst.BaseAnalyst`.
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

    Notes on configuration:
    ------------------------------
    The configuration dictionary can contain the following keywords:

    * `acceptable_mag_range`: dict
        A dictionary with upper and lower limit of the acceptable magnitude range.
        Values outside of this range will be regarded as invalid, see:
       :meth:`microlensing_ralph.analyst.light_curve_analyst.LightCurveAnalyst.flag_invalid_mags`
            Allowed keywords are:
                - `lower_limit` - lower limit of the acceptable magnitude range, default value: 40.0;
                - `upper_limit` - upper limit of the acceptable magnitude range, default value: -10.0;
    * `max_acceptable_err`: float
        A float representing the maximum acceptable error of a datapoint in the light curve,
        errors larger than that will be masked.
    * `hampel`:
        Parameters controlling the Hampel filter performing outlier marking,
        see :meth:`ralph.analyst.light_curve_analyst.LightCurveAnalyst.hampel_filter`.
            Allowed keywords are:
                - `window`: str
                    Window size (in days), as a `pandas` offset string (e.g. '3D' is 3 days),
                    half of this is applied on each side of each point.
                    Default value: `'3D'`
                - `n_sigma`: float
                    Number of standard deviations to use for the Hampel filter, used as a threshold in
                    scaled Median Absolute Deviation for flagging outliers.
                    Default value: `5.0`
                - `use_weighted`: bool
                    If `True` weighted median is used to calculate medians and MADS in the Hampel filter.
                    Default value: `False`
    * `save_outlier_results`: bool
        If `True`, results of outlier finding procedure will be saved in two files:
        `outlier_results.npz` and `outlier_sequences.json`.
        File called `outlier_results.npz` contains four arrays for each light curve.
        These arrays are:
            - 'is_outlier' - an array of flags if the point was found to be an outlier;
            - 'medians' - an array for weighted medians for windows used by the Hampel filter;
            - 'mads' - an array of MADs found in windows used by the Hampel filter;
            - 'thresholds' - an array of thresholds used by the Hampel filter to flag a point
                as an outlier.
            See: :meth:`microlensing_ralph.analyst.light_curve_analyst.LightCurveAnalyst.hampel_filter`.
        File called `outlier_sequences.json` contains a JSON file with all sequences of consecutive
        outliers found by :meth:`microlensing_ralph.analyst.light_curve_analyst.LightCurveAnalyst.vet_outliers`.

        :microlensing_ralph.analyst.light_curve_analyst.LightCurveAnalyst.flag_invalid_mags:
            Allowed models keywords are:
                - `lower_limit` - lower limit of the acceptable magnitude range;
                - `upper_limit` - upper limit of the acceptable magnitude range.
    """

    def __init__(self, event_name, analyst_path, light_curves, log, config_dict=None, config_path=None):

        super().__init__(event_name, analyst_path, config_dict=config_dict, config_path=config_path)

        self.acceptable_mag_range = None
        self.max_acceptable_err = None
        self.light_curves = light_curves
        self.log = log
        self.outlier_results = {}
        self.outlier_seqs = {}

        if config_dict is not None:
            self.config = self.parse_config(config_dict=config_dict)
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
        self.config["acceptable_mag_range"] = config_dict["lc_analyst"].get("acceptable_mag_range", None)
        self.config["max_acceptable_err"] = config_dict["lc_analyst"].get("max_acceptable_err", None)
        self.config["hampel"] = config_dict["lc_analyst"].get("hampel", None)
        self.config["save_outlier_results"] = config_dict["lc_analyst"].get("save_outlier_results", False)

        self.log.debug("LC Analyst: Finished reading lc config.")

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

    def flag_negative_errors(self, light_curve):
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
        :rtype: numpy ndarray
        """

        custom_range = self.acceptable_mag_range
        if custom_range is not None:
            mask_inv_mag = np.where(
                (light_curve[:, 1] > custom_range["upper_limit"])
                & (light_curve[:, 1] < custom_range["lower_limit"])
            )
        else:
            mask_inv_mag = np.where((light_curve[:, 1] > -10) & (light_curve[:, 1] < 40))

        return mask_inv_mag[0]

    def flag_duplicate_entries(self, light_curve):
        """
        Flags duplicate entries in the light curve.

        :param light_curve: An array containing Julian Days, magnitudes and errors
            for the whole light curve.
        :type light_curve: numpy ndarray

        :return: A mask with unique entries.
        :rtype: numpy ndarray
        """

        unique_entries, unique_index = np.unique(light_curve[:, 0], return_index=True)
        mask_unique = []
        for i in range(len(light_curve[:, 0])):
            if i in unique_index:
                mask_unique.append(True)
            else:
                mask_unique.append(False)

        return mask_unique

    def flag_huge_errors(self, light_curve):
        """
        Flags entries with huge errors.

        :param light_curve: An array containing Julian Days, magnitudes and errors
            for the whole light curve.
        :type light_curve: numpy ndarray

        :return: mask containing entries that have huge uncertainty values
        :rtype: numpy ndarray
        """

        custom_err_max = self.config["max_acceptable_err"]
        if custom_err_max is not None:
            mask_inv_err = np.where(
                (light_curve[:, 2] < custom_err_max)
            )
        else:
            mask_inv_err = np.where((light_curve[:, 2] < 1.0))

        return mask_inv_err[0]

    def perform_quality_check(self):
        """
        Performs quality checks of light curves stored in the internal dictionary,
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
            self.log.debug("LC Analyst: Applied non numerical and duplicates mask.")

            mask_inv_mags = self.flag_invalid_mags(preliminary_lc)
            preliminary_lc = preliminary_lc[mask_inv_mags]
            self.log.debug("LC Analyst: Applied mask for mags outside of range.")
            mask_inv_errs = self.flag_huge_errors(preliminary_lc)
            preliminary_lc = preliminary_lc[mask_inv_errs]
            self.log.debug("LC Analyst: Applied mask for errs outside of range ."
                           )
            mask_neg_err = self.flag_negative_errors(preliminary_lc)
            cleaned_lc = preliminary_lc[mask_neg_err]
            self.log.debug("LC Analyst: Applied masks for negative errs.")

            entry["light_curve"] = cleaned_lc

        self.log.info("LC Analyst: Quality check ended.")

    def perform_outlier_check(self):
        """
        Checks for outliers in the light curve using the Hampel filter.
        Then evaluates found outliers if they form a group of consecutive
        points. This can be used to check if they aren't candidates
        for anomalies.
        """

        self.log.info("LC Analyst: Start outlier check.")
        for entry in self.light_curves:
            # extract np array with the light curve
            lc = np.array(entry["light_curve"])
            if self.config["hampel"] is not None:
                self.outlier_results[f"{entry["survey"]}_{entry["band"]}"] = (
                    self.hampel_filter(
                        lc,
                        window=self.config["hampel"].get("window", "3D"),
                        n_sigma=self.config["hampel"].get("n_sigma", 5.0),
                        use_weighted=self.config["hampel"].get("use_weighted", False),
                    )
                )
            else:
                self.outlier_results[f"{entry["survey"]}_{entry["band"]}"] = (
                    hampel_filter(lc)
                )

            self.log.debug(f"LC Analyst: Hampel filter to look for outliers for: {entry["survey"]}_{entry["band"]}.")

            outlier_flags = self.outlier_results[f"{entry["survey"]}_{entry["band"]}"]["is_outlier"]
            self.outlier_seqs[f"{entry["survey"]}_{entry["band"]}"] = (
                vet_outliers(lc, outlier_flags)
            )
            self.log.debug(f"LC Analyst: Outliers vetted for: {entry["survey"]}_{entry["band"]}.")
            self.log.info(
                f"LC Analyst: Found {len(self.outlier_seqs)} outlier sequences for {entry["survey"]}_{entry["band"]}."
            )

        if self.config["save_outlier_results"]:
            np.savez(
                os.path.join(self.analyst_path, "outlier_results.npz"),
                self.outlier_results,
            )

            with open(os.path.join(self.analyst_path, "outlier_sequences.json"), "w", encoding="utf-8") as file:
                json.dump(self.outlier_seqs, file, ensure_ascii=False, indent=4)
            self.log.debug(f"LC Analyst: Outlier analysis results saved.")

            for entry in self.light_curves:
                lc = np.array(entry["light_curve"])
                outlier_res = self.outlier_results[f"{entry["survey"]}_{entry["band"]}"]
                outlier_seqs = self.outlier_seqs[f"{entry["survey"]}_{entry["band"]}"]
                output_fname = f"outlier_results_{entry["survey"]}_{entry["band"]}.html"
                plot_outlier_results(
                    os.path.join(self.analyst_path, output_fname),
                    f"{entry["survey"]}_{entry["band"]}",
                    lc,
                    outlier_res,
                    outlier_seqs,
                )

        self.log.info("LC Analyst: Outlier check ended.")
        return self.outlier_results, self.outlier_seqs
