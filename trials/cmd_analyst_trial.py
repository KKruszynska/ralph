# import pandas as pd
# import astroquery

# def load_gaia_data(self, parallax_quality=5):
    #     """
    #     Loads data within a specified radius and of specified parallax quality from Gaia catalogues.
    #
    #     :param catalogue_name: str, specified earlier, should contain words 'Gaia' and 'DRx',
    #     where x is the number of data release (currently supported 1, 2 and 3),
    #     for example `GaiaDR2` or `Gaia_DR3`,
    #     :param radius: float, specified earlier, radius of the search for sources around the event,
    #     :param parallax_quality: float, optional, parallax over error lower limit.
    #
    #     :return: pandas data frame with magnitudes and labels of the bands used;
    #     the bands are `Gaia_G`, `Gaia_BP`,
    #     and `Gaia_RP` corresponding to `phot_g_mean_mag`, `phot_bp_mean_mag` and `phot_rp_mean_mag`.
    #     """
    #     table_name = ''
    #     if 'DR3' in self.catalogue_name:
    #         table_name = 'gaiadr3'
    #     if 'DR2' in self.catalogue_name:
    #         table_name = 'gaiadr2'
    #     if 'DR1' in self.catalogue_name:
    #         table_name = 'gaiadr1'
    #
    #     self.log.debug('CMD Analyst: Gaia catalogue chosen for %s: %s.'%(self.catalogue_name, table_name))
    #
    #     try:
    #         if 'DR3' in self.catalogue_name:
    #             adql_query = ('SELECT source_id, phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag \
    #                                  FROM %s.gaia_source \
    #                                  WHERE parallax_over_error > %d AND \
    #                                  ruwe < 1.4 AND \
    #                                  CONTAINS(POINT(ra, dec), CIRCLE(%f, %f, %f))=1;' %
    #                           (table_name, int(parallax_quality), self.config['ra'],
    #                           self.config['dec'], self.radius))
    #         else:
    #             adql_query = ('SELECT source_id, phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag \
    #                          FROM %s.gaia_source \
    #                          WHERE parallax_over_error > %d \
    #                          CONTAINS(POINT(ra, dec), CIRCLE(%f, %f, %f))=1;'%
    #                           (table_name, int(parallax_quality),
    #                           self.config['ra'], self.config['dec'], self.radius))
    #
    #         self.log.debug('CMD Analyst: Querying Gaia.')
    #         self.log.debug('CMD Analyst: Query:\n %s'%adql_query)
    #         Gaia.load_tables(only_names=True)
    #         job = Gaia.launch_job_async(adql_query)
    #         result = job.get_results()
    #         self.log.debug('CMD Analyst: Query response retrieved.')
    #
    #         data = {'Gaia_G' : result['phot_g_mean_mag'],
    #                 'Gaia_BP' : result['phot_bp_mean_mag'],
    #                 'Gaia_RP' : result['phot_rp_mean_mag']
    #                 }
    #         data_frame = pd.DataFrame(data=data)
    #         labels = ['Gaia_G', 'Gaia_BP', 'Gaia_RP']
    #         self.log.debug('CMD Analyst: Response reformatted to dataframe, labels created.')
    #
    #     except Exception as err:
    #         self.log.exception('CMD Analyst: %s, %s' % (err, type(err)))
    #         data_frame = None
    #         labels = None
    #
    #     return data_frame, labels