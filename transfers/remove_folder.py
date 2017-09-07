#!/usr/bin/env python
"""
Automate Transfers

Helper script to automate running transfers through Archivematica.
"""

from __future__ import print_function, unicode_literals

import logging
import os
import shutil
import sys
import requests

from transfers import utils, models

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(THIS_DIR)

LOG_NAME = 'remove_folder'
LOGGER = logging.getLogger(LOG_NAME)


def get_source_location(ss_url, ss_user, ss_api_key, ts_location_uuid):
    """
    Retrieve the path of the source location
    :param ss_url: URL of the Storage Sevice to query
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


def get_status(am_url, am_user, am_api_key, unit_uuid, hide_on_complete=False):
    """
    Get status of the SIP or Transfer with unit_uuid.

    :param str unit_uuid: UUID of the unit to query for.
    :param str unit_type: 'ingest' or 'transfer'
    :param bool hide_on_complete: If True, hide the unit in the dashboard if COMPLETE
    :returns: Dict with status of the unit from Archivematica or None.
    """
    # Get status
    url = am_url + '/api/ingest/status/' + unit_uuid + '/'
    params = {'username': am_user, 'api_key': am_api_key}
    unit_info = utils.call_url_json(url, params)

    # If complete, hide in dashboard
    if hide_on_complete and unit_info and unit_info['status'] == 'COMPLETE':
        LOGGER.info('Hiding SIP %s in dashboard', unit_uuid)
        url = am_url + '/api/ingest/' + unit_uuid + '/delete/'
        LOGGER.debug('Method: DELETE; URL: %s; params: %s;', url, params)
        response = requests.delete(url, params=params, verify=(utils.get_setting('ssl_verification', 'True')) == 'True')
        LOGGER.debug('Response: %s', response)

    return unit_info


def remove_folder(directory, depth):
    assert directory
    # Better be damned sure this is a path with a couple of separators
    separators = sum(1 for sep in directory if sep == '/')
    if separators < depth:
        LOGGER.error('Cannot remove directories that are root or %s levels down.', depth)
        return False

    if os.path.exists(directory):
        try:
            LOGGER.info('Remove directory attempt %s', directory)
            shutil.rmtree(directory, ignore_errors=False)
            return True
        except OSError as e:
            LOGGER.error('Unable to remove directory %s', directory)
            return False
    else:
        LOGGER.warning('No such directory to remove: %s', directory)
        return True


def main(am_user, am_api_key, ss_user, ss_api_key, ts_uuid, am_url, ss_url, depth, hide_on_complete=False,
         see_files=False, config_file=None, log_level='INFO', **kwargs):
    utils.setup(config_file, LOG_NAME, log_level)
    LOGGER.info("Waking up")

    session = models.Session()

    # Check for evidence that this is already running
    default_pidfile = os.path.join(THIS_DIR, LOG_NAME + '.pid.lck')
    pid_file = utils.get_setting('remove_pidfile', default_pidfile)
    if not utils.set_pid_file(pid_file):
        return 0

    source_location = get_source_location(ss_url, ss_user, ss_api_key, ts_uuid)

    current_units = []
    try:
        current_units = session.query(models.Unit).filter_by(current=True, unit_type='ingest').all()
    except Exception:
        LOGGER.debug('Query failed for current units', exc_info=True)
        LOGGER.info('Assuming new run.')

    for current_unit in current_units:
        LOGGER.info('Current unit: %s', current_unit)

        unit_uuid = current_unit.uuid
        unit_path = current_unit.path

        # Get status
        status_info = get_status(am_url, am_user, am_api_key, unit_uuid, hide_on_complete)
        LOGGER.info('Status info: %s', status_info)
        if not status_info:
            LOGGER.error('Could not fetch status for %s. Exiting.', unit_uuid)
            break

        status = status_info.get('status')
        current_unit.status = status

        if status == 'COMPLETE':
            unit = os.path.dirname(unit_path) if see_files else unit_path
            directory = source_location + '/' + unit
            LOGGER.info('Current transfer completed. Removing package from transfer source %s', directory)
            if remove_folder(directory, depth):
                session.delete(current_unit)

    session.commit()
    os.remove(pid_file)
    return 0  # always return a zero.


if __name__ == '__main__':
    utils.main(main)
