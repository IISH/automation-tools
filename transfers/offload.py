#!/usr/bin/env python
#
# Offload
#
# Check to see if the offload is completed for each item in the list.
# A completed offload has:
# 1a. a checksum for each file
# 1b. OR an ingest.txt file in de folder.
# 2. Confirmation by the catalog API to make sure the file in question exists.
#
# Dependencies:
# accession_exists
# text_identifier_accession

import hashlib
import logging
import os

import utils, get_accession_number

LOGGER = None


def find_accession_number(accession_number):
    url = os.getenv('CATALOG_ENDPOINT', 'http://localhost:8080') + '/service/all'
    params = {'access_token': os.getenv('CATALOG_KEY', 'dummy')}
    LOGGER.info('Verify existing ' + accession_number)
    data = utils.call_url_json(url, params)
    if data['collections']:
        return [ac for ac in data['collections'] if ac == accession_number]
    else:
        LOGGER.error('Empty list')
        return None


# Calculate the hash by streaming the file
def hashfile(file, blocksize=32768):
    _file = open(file, 'r')
    _blocksize = blocksize
    hasher = hashlib.md5()
    while _blocksize == blocksize:
        buf = _file.read(blocksize)
        hasher.update(buf)
        _blocksize = len(buf)

    _file.close()
    return hasher.hexdigest()


def checksum(file):
    file_md5 = file + ".md5"
    with open(file_md5, 'r') as fs:
        expected_hash = fs.readline().split(' ')[0]  # Comes in the form: [md5]  [filename]
    actual_hash = hashfile(file)
    if expected_hash == actual_hash:
        LOGGER.info('OK... ' + file)
        return True
    else:
        LOGGER.error('ERROR... expect ' + expected_hash + ' but got ' + actual_hash + ' for file ' + file)
        utils.send_mail(
            'Failed to validate FTP offload',
            'Failed to validate FTP offload ' + file + '. Hash expected ' + expected_hash + ' but got ' + actual_hash
        )
        return False


def file(entry):
    if os.path.exists(entry) and os.path.isfile(entry) \
            and not entry.endswith('.md5') and not entry.endswith('ingest.txt'):
        directory = os.path.dirname(entry)
        files = [os.path.join(directory, f) for f in os.listdir(directory) if
                 os.path.isfile(os.path.join(directory, f))]
        if os.path.join(directory, 'ingest.txt') in files:
            LOGGER.info('Found ' + os.path.join(directory, 'ingest.txt'))
            return True
        elif entry + '.md5' in files:
            return checksum(entry)
        else:
            LOGGER.info('As of yet no checksum file found for ' + entry)
            return False
    else:
        LOGGER.info('Path not found: ' + entry)
        return False


def main(source_location, candidates, log_name):
    global LOGGER
    LOGGER = logging.getLogger(log_name)

    selected = set()
    for entry in candidates:
        location_entry = source_location + '/' + entry.decode('utf-8')
        LOGGER.debug('offload.download_complete ' + location_entry)
        an = get_accession_number.parse(location_entry)
        if an and find_accession_number(an) and file(location_entry):
            selected.add(entry)
    return selected
