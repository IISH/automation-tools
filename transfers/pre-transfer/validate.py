#!/usr/bin/env python
#
# validate.py
#
# Validates a folder structure
import getopt
import os
import sys
from preservation import Preservation
from error import Error


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
            if folder in Preservation.FILE_GROUP:
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
        contains_inv_numbers = None
        for folder in folders:
            for item in os.listdir(self.fileset + '/' + folder):
                if contains_inv_numbers is None:
                    contains_inv_numbers = os.path.isdir(self.fileset + '/' + folder + '/' + item)

                if contains_inv_numbers is not os.path.isdir(self.fileset + '/' + folder + '/' + item):
                    self.error(Error.MIXED_INV_NO, Error.MIXED_INV_NO_MSG)
                    return

        if contains_inv_numbers:
            self.type = 'archive'

        # --------------------------------------------------------------------------------------------------------------
        # Validate 6:
        # All filenames should match the convention
        # --------------------------------------------------------------------------------------------------------------
        if self.type == 'archive':
            for folder in folders:
                for inv_no in os.listdir(self.fileset + '/' + folder):
                    for filename in os.listdir(self.fileset + '/' + folder + '/' + inv_no):
                        item = filename.split('_', 1)
                        if len(item) != 2 or item[0] != accession_id + '.' + inv_no or item[1].isdigit():
                            self.error(Error.INVALID_FILENAME,
                                       Error.INVALID_FILENAME_MSG.format(filename,
                                                                         accession_id + '.' + inv_no + '_'))
        else:
            for folder in folders:
                for filename in os.listdir(self.fileset + '/' + folder):
                    item = filename.split('_', 1)
                    if len(item) != 2 or item[0] != accession_id or item[1].isdigit():
                        self.error(Error.INVALID_FILENAME,
                                   Error.INVALID_FILENAME_MSG.format(filename,
                                                                     accession_id + '_'))
        if self.report['error']:
            return

        # --------------------------------------------------------------------------------------------------------------
        # Validate 7:
        # Files in the other groups should be in the preservation group
        # --------------------------------------------------------------------------------------------------------------
        all_filenames = []
        for root, dirs, files in os.walk(self.fileset + '/preservation'):
            all_filenames.extend([os.path.basename(file) for file in files])
        for root, dirs, files in os.walk(self.fileset):
            for file in files:
                if not os.path.basename(file) in all_filenames:
                    self.error(Error.NO_PRESERVATION_FILE,
                               Error.NO_PRESERVATION_FILE_MSG.format(file))
        if self.report['error']:
            return


def unit_tests():
    print('Run unit tests.')

    this_dir = os.path.abspath(os.path.dirname(__file__))
    tests = {'ARCH1': Error.EMPTY_FOLDER, 'ARCH2': Error.NO_GROUPS, 'ARCH3': Error.UNKNOWN_GROUPS,
             'ARCH4': Error.PRESERVATION_FOLDER_MISSING, 'ARCH5': Error.MIXED_INV_NO,
             'ARCH6': Error.INVALID_FILENAME, 'ARCH7': Error.NO_PRESERVATION_FILE,
             'ARCH0': 0}
    errors = 0
    # noinspection PyCompatibility
    for key, value in tests.iteritems():
        validate = ValidateFolder((this_dir + '/tests/' + key))
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


if __name__ == '__main__':
    main(sys.argv[1:])
