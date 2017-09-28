#!/usr/bin/env python
"""
Create folders

Helper script to add upload folders.
"""

from __future__ import print_function
import os
import logging

import utils

LOG_NAME = 'add_folder'
LOGGER = logging.getLogger(LOG_NAME)


def get_source_location(ss_url, ss_user, ss_api_key, ts_location_uuid):
    """
    Retrieve the path of the source location
    :param ss_url: URL of the Storage Service to query
    :param ss_user: User on the Storage Service for authentication
    :param ss_api_key: API key for user on the Storage Service for authentication
    :param ts_location_uuid: UUID of the transfer source Location
    :return: Path to TS Location
    """
    url = ss_url + '/api/v2/location/' + ts_location_uuid + '/'
    params = {
        'username': ss_user,
        'api_key': ss_api_key,
    }
    location_info = utils.call_url_json(url, params)
    if location_info is None:
        LOGGER.info('No location returned from transfer source ' + ts_location_uuid)
        return None
    else:
        return location_info['path']


def _add_directory(source_location, accession_number):
    directory = os.path.join(source_location, accession_number)
    if os.path.exists(directory):
        LOGGER.info('Directory exists, skipping: ' + directory)
    else:
        LOGGER.info('Creating: ' + directory)
        os.makedirs(directory)
        stat_info = os.stat(source_location)
        cur_dir = accession_number
        while cur_dir:
            os.chown(os.path.join(source_location, cur_dir), stat_info.st_uid, stat_info.st_gid)
            os.chmod(os.path.join(source_location, cur_dir), stat_info.st_mode)
            cur_dir, dir = os.path.split(cur_dir)


def main(ss_user, ss_api_key, ts_uuid, ss_url, config_file=None, log_level='INFO', **kwargs):
    """
    Find the accession number and create the appropriate folder for it.
    """
    utils.setup(config_file, LOG_NAME, log_level)
    source_location = get_source_location(ss_url, ss_user, ss_api_key, ts_uuid)
    url = utils.get_setting('catalog_endpoint', 'http://localhost:8080') + '/service/all'
    params = {'access_token': utils.get_setting('catalog_key', 'dummy')}
    data = utils.call_url_json(url, params)
    if data['collections']:
        for accession_number in data['collections']:
            _add_directory(source_location, accession_number.replace('.', '/'))
    else:
        LOGGER.warning('Empty list')
        return None


if __name__ == '__main__':
    utils.main(main)
