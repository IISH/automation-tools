from __future__ import print_function, unicode_literals
import argparse
import logging
import logging.config  # Has to be imported separately
import os
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from six.moves import configparser
import sys

import models

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(THIS_DIR)

LOGGER = None
CONFIG_FILE = None

try:
    from os import fsencode, fsdecode
except ImportError:
    # Cribbed & modified from Python3's OS module to support Python2
    def fsencode(filename):
        encoding = sys.getfilesystemencoding()
        if isinstance(filename, str):
            return filename
        elif isinstance(filename, unicode):
            return filename.encode(encoding)
        else:
            raise TypeError("expect bytes or str, not %s" % type(filename).__name__)


    def fsdecode(filename):
        encoding = sys.getfilesystemencoding()
        if isinstance(filename, unicode):
            return filename
        elif isinstance(filename, str):
            return filename.decode(encoding)
        else:
            raise TypeError("expect bytes or str, not %s" % type(filename).__name__)


def get_setting(setting, default=None):
    config = configparser.SafeConfigParser()
    try:
        config.read(CONFIG_FILE)
        return config.get('transfers', setting)
    except Exception:
        return default


def add_env():
    config = configparser.SafeConfigParser()
    try:
        config.read(CONFIG_FILE)
        items = config.items('transfers')
        for key, value in items:
            os.environ[key.upper()] = value
    except Exception:
        return


def call_url_json(url, params):
    """
    Helper to GET a URL where the expected response is 200 with JSON.

    :param str url: URL to call
    :param dict params: Params to pass to requests.get
    :returns: Dict of the returned JSON or None
    """
    LOGGER.debug('URL: %s; params: %s;', url, params)
    response = requests.get(url, params=params, verify=(get_setting('ssl_verification', 'True')) == 'True')
    LOGGER.debug('Response: %s', response)
    if not response.ok:
        LOGGER.warning('Request to %s returned %s %s', url, response.status_code, response.reason)
        LOGGER.debug('Response: %s', response.text)
        return None
    try:
        return response.json()
    except ValueError:  # JSON could not be decoded
        LOGGER.warning('Could not parse JSON from response: %s', response.text)
        return None


def set_pid_file(pid_file):
    # Check for evidence that this is already running
    try:
        # Open PID file only if it doesn't exist for read/write
        f = os.fdopen(os.open(pid_file, os.O_CREAT | os.O_EXCL | os.O_RDWR), 'r+')
    except:
        LOGGER.info('This script is already running. To override this behaviour and start a new run, remove %s',
                    pid_file)
        return False
    else:
        pid = os.getpid()
        f.write(str(pid))
        f.close()
        return True


def setup(config_file, log_name, log_level):
    global CONFIG_FILE
    CONFIG_FILE = config_file
    models.init(get_setting('databasefile', os.path.join(THIS_DIR, 'transfers.db')))

    # Configure logging
    default_logfile = os.path.join(THIS_DIR, 'automate-transfer.log')
    CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(levelname)-8s  %(asctime)s  %(name)-12s %(filename)s:%(lineno)-4s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': get_setting('logfile', default_logfile),
                'backupCount': 2,
                'maxBytes': 10 * 1024,
            },
        },
        'loggers': {
            log_name: {
                'level': log_level,
                'handlers': ['console', 'file'],
            },
        },
    }
    logging.config.dictConfig(CONFIG)

    global LOGGER
    LOGGER = logging.getLogger(log_name)

    # Add the configuration to the environment
    add_env()


def main(script):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-u', '--user', metavar='USERNAME', required=True,
                        help='Username of the Archivematica dashboard user to authenticate as.')
    parser.add_argument('-k', '--api-key', metavar='KEY', required=True,
                        help='API key of the Archivematica dashboard user.')
    parser.add_argument('--ss-user', metavar='USERNAME', required=True,
                        help='Username of the Storage Service user to authenticate as.')
    parser.add_argument('--ss-api-key', metavar='KEY', required=True, help='API key of the Storage Service user.')
    parser.add_argument('-t', '--transfer-source', metavar='UUID', required=True,
                        help='Transfer Source Location UUID to fetch transfers from.')
    parser.add_argument('--transfer-path', metavar='PATH', help='Relative path within the Transfer Source. Default: ""',
                        type=fsencode, default=b'')  # Convert to bytes from unicode str provided by command line
    parser.add_argument('--depth', '-d',
                        help='Depth to create the transfers from relative to the transfer source location and path. Default of 1 creates transfers from the children of transfer-path.',
                        type=int, default=1)
    parser.add_argument('--am-url', '-a', metavar='URL', help='Archivematica URL. Default: http://127.0.0.1',
                        default='http://127.0.0.1')
    parser.add_argument('--ss-url', '-s', metavar='URL', help='Storage Service URL. Default: http://127.0.0.1:8000',
                        default='http://127.0.0.1:8000')
    parser.add_argument('--transfer-type', metavar='TYPE',
                        help="Type of transfer to start. One of: 'standard' (default), 'unzipped bag', 'zipped bag', 'dspace'.",
                        default='standard', choices=['standard', 'unzipped bag', 'zipped bag', 'dspace'])
    parser.add_argument('--files', action='store_true', help='If set, start transfers from files as well as folders.')
    parser.add_argument('--hide', action='store_true',
                        help='If set, hide the Transfers and SIPs in the dashboard once they complete.')
    parser.add_argument('-c', '--config-file', metavar='FILE', help='Configuration file(log/db/PID files)',
                        default=None)

    # Logging
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase the debugging output.')
    parser.add_argument('--quiet', '-q', action='count', default=0, help='Decrease the debugging output')
    parser.add_argument('--log-level', choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'], default=None,
                        help='Set the debugging output level. This will override -q and -v')

    args = parser.parse_args()

    log_levels = {
        2: 'ERROR',
        1: 'WARNING',
        0: 'INFO',
        -1: 'DEBUG',
    }
    if args.log_level is None:
        level = args.quiet - args.verbose
        level = max(level, -1)  # No smaller than -1
        level = min(level, 2)  # No larger than 2
        log_level = log_levels[level]
    else:
        log_level = args.log_level

    sys.exit(script(
        am_user=args.user,
        am_api_key=args.api_key,
        ss_user=args.ss_user,
        ss_api_key=args.ss_api_key,
        ts_uuid=args.transfer_source,
        ts_path=args.transfer_path,
        depth=args.depth,
        am_url=args.am_url,
        ss_url=args.ss_url,
        transfer_type=args.transfer_type,
        see_files=args.files,
        hide_on_complete=args.hide,
        config_file=args.config_file,
        log_level=log_level,
    ))
