#!/usr/bin/env python
#
# Storage
#
# Determine the available storage on the shared directory and calculate the threshold.

from __future__ import print_function
import logging
import os

LOGGER = None


def get_size(start_path='/'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                total_size += 0
    return total_size


def main(shared_location_path, shared_location_quota, location_entry, candidates, log_name, storage_cap=2):
    global LOGGER
    LOGGER = logging.getLogger(log_name)

    assert storage_cap > 0

    selected = set()
    for entry in candidates:
        used = get_size(shared_location_path)
        available = shared_location_quota - used
        package_size = get_size(location_entry + '/' + entry)
        needed = package_size * storage_cap

        LOGGER.info('shared storage location %s used %s available %s', shared_location_path, used, available)
        LOGGER.info('Estimated size needed: %s')

        if needed < available:
            selected.add(entry)
        else:
            LOGGER.info('Package size exceeds quota')
    return selected
