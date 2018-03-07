#!/usr/bin/env python
#
# List the contents of the database.

from __future__ import print_function, unicode_literals

import logging
import os
import sys

import utils, models

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(THIS_DIR)

LOG_NAME = 'list_db'
LOGGER = logging.getLogger(LOG_NAME)

def main(config_file=None, log_level='INFO', **kwargs):
    utils.setup(config_file, LOG_NAME, log_level)
    LOGGER.info("Database content")

    session = models.Session()
    records = session.query(models.Unit).all()
    for record in records:
        print(record)

    return 0  # always return a zero.

if __name__ == '__main__':
    utils.main(main)
