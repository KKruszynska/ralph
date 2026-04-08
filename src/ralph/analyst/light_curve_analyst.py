from time import sleep
import numpy as np

from MFPipeline.analyst.analyst import Analyst

class LightCurveAnalyst(Analyst):
    """
    This is a class that performs light curve
    It is a child of the :class:`MFPipeline.analyst.analyst.Analyst`
    It follows a flowchart specified here: link link link

    A Fit Analyst needs either a config_path or config_dict, otherwise it will not work.

    :param event_name: str, name of the analyzed event
    :param analyst_path: str, path to the folder where the outputs are saved
    :param light_curves: list, a list containing light curves, observatory name, and filter
    :param log: logger instance, log started by Event Analyst
    :param config_dict: dictionary, optional, dictionary with Event Analyst configuration
    :param config_path: str, optional, path to the YAML configuration file of the Event Analyst
    """
    def __init__(self,
                 event_name,
                 analyst_path,
                 light_curves,
                 log,
                 config_dict=None,
                 config_path=None):

        super().__init__(event_name, analyst_path, config_dict=config_dict, config_path=config_path)
        # Analyst.__init__(self, event_name, analyst_path, config_dict=config_dict, config_path=config_path)

        self.acceptable_mag_range = None
        self.light_curves = light_curves
        self.log = log

        if (config_dict != None):
            self.add_lc_config(config_dict)
        elif("lc_analyst" in self.config):
            self.add_lc_config(self.config)
        else:
            self.log.error("LC Analyst: Error! Light Curve Analyst needs information.")
            quit()


    def add_lc_config(self, config):
        """
        Add LC configuration fields to analyst config.

        :param config_dict: dict, dictionary with analyst config
        """

        self.log.debug("LC Analyst: Reading lc config.")
        self.acceptable_mag_range = config["lc_analyst"].get("acceptable_mag_range", None)
        self.log.debug("LC Analyst: Finished reading lc config.")

    def perform_quality_check(self):
        """
        Performing a quality check of the light curve and applying masks to invalid entries.
        A cleaned light curve will replace the old entry.

        :return:
        """

        status = False

        self.log.info("LC Analyst: Start quality check.")
        for entry in self.light_curves:
            #extract np array with the light curve
            lc = np.array(entry["lc"])

            self.log.debug("LC Analyst: Masking bad data.")
            mask_duplicate = self.flag_duplicate_entries(lc)
            mask_inf_entry = self.flag_infinite_entries(lc)
            prel_mask = np.logical_and(mask_inf_entry, mask_duplicate)
            prel_lc = lc[prel_mask]
            self.log.debug("LC Analyst: Applying non numerical and duplicates mask.")

            mask_inv_mags = self.flag_invalid_mags(prel_lc)
            self.log.debug("LC Analyst: Applying bad data mask.")
            cleaned_lc = prel_lc[mask_inv_mags]

            mask_neg_err = self.flag_negative_errorbars(prel_lc)
            fin_lc = cleaned_lc[mask_neg_err]
            entry["lc"] = fin_lc
        self.log.info("LC Analyst: Quality check ended.")


    def flag_infinite_entries(self, light_curve):
        '''
        Flags entries with non-finite values. Similar like in pyLIMA.
        :param light_curve: numpy array, an array containing JD, magnitude and error
        :return: mask with entries that don't have invalid magnitudes
        '''
        mask_finite_mag = np.isfinite(light_curve[:,1])
        mask_finite_err = np.isfinite(light_curve[:, 2])
        final_mask = np.logical_and(mask_finite_mag, mask_finite_err)

        return final_mask

    def flag_huge_errorbars(self, light_curve):
        """
        Flag entries with huge errorbars.
        :param light_curve: numpy array, an array containing JD, magnitude and error
        :return: mask containing entries that have huge uncertianity values
        """

        return 0.

    def flag_negative_errorbars(self, light_curve):
        """
        Flags entries with negative errorbars.
        :param light_curve: numpy array, an array containing JD, magnitude and error
        :return: mask with entries that don't have negative uncertianities
        """
        mask_neg_err = np.where(light_curve[:, 2] > 0)

        return mask_neg_err

    def flag_invalid_mags(self, light_curve):
        """
        Flags entries with magnitudes smaller than -10. Many surveys indicate an invalid entry
        by applying -99 or 99 to the light curves.
        :param light_curve: numpy array, an array containing JD, magnitude and error
        :return: mask with entries that don't have invalid magnitudes
        """
        custom_range = self.acceptable_mag_range
        if custom_range is not None:
            mask_inv_mag = np.where((light_curve[:, 1] > custom_range["upper_limit"]) & (light_curve[:, 1] < custom_range["lower_limit"]))
        else:
            mask_inv_mag = np.where((light_curve[:, 1] > -10) & (light_curve[:, 1] < 40))

        return mask_inv_mag

    def flag_duplicate_entries(self, light_curve):
        """
        Flags duplicate entries in the light curve.
        :param light_curve: numpy array, an array containing JD, magnitude and error
        :return: mask with entries that are not duplicated
        """
        unique_entries, unique_index = np.unique(light_curve[:,0], return_index = True)
        mask_unique = []
        for i in range(len(light_curve[:,0])):
            if i in unique_index:
                mask_unique.append(True)
            else:
                mask_unique.append(False)

        return mask_unique
