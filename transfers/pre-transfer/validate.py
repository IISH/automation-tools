#!/usr/bin/env python
# coding=utf-8
#
# validate.py
#
# Validates a folder structure. Each folder should conform to this convention:
#
# naming authority
#  [ARCHIVAL INVENTORY].[NUMBER]/[GROUP (unique and repeatable)]/[ARCHIVAL INVENTORY].[NUMBER]_[SEQUENCE].[EXTENSION]
#
# Example: validate "10622/ARCH00842.1"
# 10622
# ├── ARCH00842.1
# │   └── preservation
# │       ├── ARCH00842.1_0001.tif
# │       └── ARCH00842.1_0002.tif

import getopt
import os
import sys
from preservation import Preservation
from error import Error
import re


class ValidateFolder:
    fileset = None
    type = 'default'
    report = {'error': list(), 'info': list(), 'codes': list()}

    def __init__(self, fileset):
        self.fileset = fileset

    def clear(self):
        self.report['codes'] = []
        self.report['error'] = []
        self.report['info'] = []

    def info(self, text):
        self.report['info'].append(text)
        print(text)

    def error(self, code, text):
        self.report['codes'].append(code)
        self.report['error'].append(text)
        print(str(code) + ': ' + text)

    def run(self):
        accession_id = os.path.basename(self.fileset)

        self.info("Accession ID = " + accession_id)

        if os.path.isfile(self.fileset):
            self.type = 'single'
            return

        # --------------------------------------------------------------------------------------------------------------
        # Validate 1: must have content
        # --------------------------------------------------------------------------------------------------------------
        if not os.listdir(self.fileset):
            return self.error(Error.EMPTY_FOLDER, Error.EMPTY_FOLDER_MSG.format(self.fileset))

        folders = [directory for directory in os.listdir(self.fileset) if
                   os.path.isdir(self.fileset + '/' + directory)]

        # --------------------------------------------------------------------------------------------------------------
        # Validate 2: a fileset cannot be empty
        # --------------------------------------------------------------------------------------------------------------
        if folders:
            self.info("Found {} file groups".format(len(folders)))
        else:
            return self.error(Error.NO_GROUPS, Error.NO_GROUPS_MSG.format(self.fileset))

        # --------------------------------------------------------------------------------------------------------------
        # Validate 3:
        # All folders in the fileset must conform to known fileGroup use types.
        # --------------------------------------------------------------------------------------------------------------
        for folder in folders:
            if folder in Preservation.FILE_GROUP or folder in Preservation.FILE_ACCESS_GROUP:
                self.info("Ok... FileGroup {}".format(folder))
            else:
                self.error(Error.UNKNOWN_GROUPS,
                           Error.UNKNOWN_GROUPS_MSG.format(folder, Preservation))
        if self.report['error']:
            return

        # --------------------------------------------------------------------------------------------------------------
        # Validate 4: The group 'preservation' is mandatory
        # --------------------------------------------------------------------------------------------------------------
        if 'preservation' in folders:
            self.info("Ok... preservation folder found")
        else:
            return self.error(Error.PRESERVATION_FOLDER_MISSING, Error.PRESERVATION_FOLDER_MISSING_MSG)

        # --------------------------------------------------------------------------------------------------------------
        # Validate 5:
        # If there are folders with inventory numbers, all files should be in an inventory number folder
        # --------------------------------------------------------------------------------------------------------------
        self.type = 'archive'

        # --------------------------------------------------------------------------------------------------------------
        # Validate 6:
        # All filenames should match the convention
        # --------------------------------------------------------------------------------------------------------------
        pattern = '^[a-zA-Z0-9]+\\.[0-9]+_[0-9]*\\.[a-zA-Z]+$'
        compiled_pattern = re.compile(pattern)
        for folder in folders:
            if folder in Preservation.FILE_GROUP:
                for filename in os.listdir(self.fileset + '/' + folder):
                    if compiled_pattern.match(filename):
                        self.info("Ok... {}".format(filename))
                    else:
                        self.error(Error.INVALID_FILENAME,
                                   Error.INVALID_FILENAME_MSG.format(filename, pattern))
        if self.report['error']:
            return

        # --------------------------------------------------------------------------------------------------------------
        # Validate 7:
        # Files in the other groups should be in the preservation group
        # --------------------------------------------------------------------------------------------------------------
        all_filenames = []
        for root, dirs, files in os.walk(self.fileset + '/preservation'):
            all_filenames.extend([os.path.splitext(f)[0] for f in files])
        for root, dirs, files in os.walk(self.fileset):
            for f in files:
                if not os.path.splitext(f)[0] in all_filenames:
                    self.error(Error.NO_PRESERVATION_FILE,
                               Error.NO_PRESERVATION_FILE_MSG.format(f))
        if self.report['error']:
            return

        # Same for access copies
        if os.path.isdir(self.fileset + '/access'):
            access_copies = os.listdir(self.fileset + '/access')
            for access_copy in access_copies:
                all_filenames = []
                for root, dirs, files in os.walk(self.fileset + '/access/' + access_copy):
                        all_filenames.extend([os.path.splitext(f)[0] for f in files])
                for root, dirs, files in os.walk(self.fileset):
                    for f in files:
                        if not os.path.splitext(f)[0] in all_filenames:
                            self.error(Error.NO_PRESERVATION_FILE,
                                       Error.NO_PRESERVATION_FILE_MSG.format(f))
            if self.report['error']:
                return

        # --------------------------------------------------------------------------------------------------------------
        # Validate 8:
        # Ensure our sequences are indeed numeric.
        # --------------------------------------------------------------------------------------------------------------
        for folder in folders:
            files = set()
            if folder in Preservation.FILE_GROUP:
                for item in os.listdir(self.fileset + '/' + folder):  # item is a file: ARCH12345.6_00001.tif
                    sequence = item.split("_")[1]  # 00001.tif
                    sequence = sequence.split(".")[0]  # 00001
                    if sequence.isdigit():
                        sequence = int(sequence)
                        if sequence in files:
                            self.error(Error.SEQUENCE_NOT_UNIQUE, Error.SEQUENCE_NOT_UNIQUE_MSG.format(sequence))
                        else:
                            files.add(sequence)

                    else:
                        self.error(Error.INVALID_FILENAME, Error.INVALID_FILENAME_MSG.format(item, accession_id + '_'))

                if self.report['error']:
                    return

                # ----------------------------------------------------------------------------------------------------------
                # Validate 9:
                # Does the set start with an element 1?
                # ----------------------------------------------------------------------------------------------------------
                sorted_list = sorted(files, key=int)
                if sorted_list[0] != 1:
                    self.error(Error.SEQUENCE_DOES_NOT_START_WITH_1, Error.SEQUENCE_DOES_NOT_START_WITH_1_MSG)
                    return

                # ----------------------------------------------------------------------------------------------------------
                # Validate 10:
                # Does the set increment with 1?
                # ----------------------------------------------------------------------------------------------------------
                for index in range(0, len(sorted_list)):
                    expect = index + 1
                    actual = sorted_list[index]
                    if expect != actual:
                        self.error(Error.SEQUENCE_INTERVAL_NOT_1, Error.SEQUENCE_INTERVAL_NOT_1_MSG.format(expect, actual))

                if self.report['error']:
                    return

    def exitcode(self):
        return len(self.report['error'])


def unit_tests():
    print('Run unit tests.')

    this_dir = os.path.abspath(os.path.dirname(__file__))
    tests = {'ARCH67890.1': Error.EMPTY_FOLDER, 'ARCH67890.2': Error.NO_GROUPS, 'ARCH67890.3': Error.UNKNOWN_GROUPS,
             'ARCH67890.4': Error.PRESERVATION_FOLDER_MISSING,  # 'ARCH67890.5': Error.MIXED_INV_NO,
             'ARCH67890.6': Error.INVALID_FILENAME, 'ARCH67890.7': Error.NO_PRESERVATION_FILE,
             'ARCH67890.8': Error.SEQUENCE_NOT_UNIQUE, 'ARCH67890.9': Error.SEQUENCE_DOES_NOT_START_WITH_1,
             'ARCH67890.10': Error.SEQUENCE_INTERVAL_NOT_1,
             'ARCH67890.0': 0}
    errors = 0
    # noinspection PyCompatibility
    for key, value in tests.iteritems():
        validate = ValidateFolder((this_dir + '/tests/12345/' + key))
        validate.run()
        if not value or value in validate.report['codes']:
            print("OK... {} {} {}".format(key, value, validate.report['error']))
        else:
            print("BAD... Expected {} {} but got no report of a validation failure".format(key, value))
            errors = errors + 1
        print('')
        validate.clear()

    if errors:
        print("FAIL... {} out of {}".format(errors, len(tests)))
        sys.exit(-1)
    else:
        print("SUCCESS... {} out of {}".format(len(tests), len(tests)))
        sys.exit(0)


def usage():
    print('Usage: validate.py --fileset [fileSet] or test')


def main(argv):
    fileset = None
    test = False

    try:
        opts, args = getopt.getopt(argv, 'f:t:h', ['fileset=', 'test', 'help'])
    except getopt.GetoptError as e:
        print("Opt error: " + e.msg)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        if opt in ('-f', '--fileset'):
            fileset = arg
        if opt in ('-t', '--test'):
            test = True

    if test:
        unit_tests()
    else:
        assert fileset
        validate = ValidateFolder(fileset)
        validate.run()
        sys.exit(validate.exitcode())


if __name__ == '__main__':
    main(sys.argv[1:])
