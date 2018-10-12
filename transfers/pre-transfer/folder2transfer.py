#!/usr/bin/env python
#
# folder2transfer.py
#
# Reconstructs a folder structure into a conventional transfer structure
#
# The folder setup is:
# [Preservation type: one of Audio, Archive, Books, Serial, Poster
# [ARCHIVAL ID]
# [ARCHIVAL ID]/manifest.csv
#     folder[r=repeatable]
#         [Inventory number][r]
#             [Files][r]
#
# The end result is a csv file called:
# [ARCHIVAL ID]/ARCHIVAL ID.good.csv
import getopt
import os
import sys
from preservation import Preservation
from error import Error


class Csv2Mets:
    fileset = None
    report = {'error': list(), 'info': list(), 'codes': list()}

    def __init__(self, fileset):
        self.fileset = fileset

    def info(self, text):
        self.report['info'].append(text)

    def error(self, code, text):
        self.report['codes'].append(code)
        self.report['error'].append(text)

    def run(self):
        accession_id = os.path.basename(self.fileset)

        self.info("Accession ID = " + accession_id)

        # ---------------------------------------------------------------------------------------------------
        # validate 1: must have a manifest
        # ---------------------------------------------------------------------------------------------------
        manifest_file = self.fileset + '/manifest.csv'
        if not os.path.exists(manifest_file):
            return self.error(Error.NO_MANIFEST, Error.NO_MANIFEST_MSG.format(manifest_file))

        file_groups = [directory for directory in os.listdir(self.fileset) if os.path.isdir(self.fileset + '/' + directory)]

        # ---------------------------------------------------------------------------------------------------
        # validate 2: a fileset cannot be empty
        # ---------------------------------------------------------------------------------------------------
        if file_groups:
            self.info("Found {} file groups".format(len(file_groups)))
        else:
            return self.error(Error.NO_GROUPS, Error.NO_GROUPS_MSG.format(self.fileset))

        # ---------------------------------------------------------------------------------------------------
        # Validate 3:
        # All file_groups in the fileset must conform to known fileGroup uses.
        # ---------------------------------------------------------------------------------------------------
        for folder in file_groups:
            if folder in Preservation.FILE_GROUP:
                self.info("Ok... FileGroup %s".format(folder))
            else:
                self.error(Error.UNKNOWN_GROUPS,
                           Error.UNKNOWN_GROUPS_MSG.format(folder, Preservation))
        if self.report['error']:
            return

        # ---------------------------------------------------------------------------------------------------
        # Validate 4:
        # All file_groups in the fileset must conform to known fileGroup uses.
        # ---------------------------------------------------------------------------------------------------


def unit_tests():
    print('Run unit tests.')

    this_dir = os.path.abspath(os.path.dirname(__file__))
    tests = {'ARCH1': Error.NO_MANIFEST, 'ARCH2': Error.NO_GROUPS, 'ARCH3': Error.UNKNOWN_GROUPS}

    errors = 0
    # noinspection PyCompatibility
    for key, value in tests.iteritems():
        csv2mets = Csv2Mets((this_dir + '/tests/' + key))
        csv2mets.run()
        if value in csv2mets.report['codes']:
            print("OK... {} {}".format(key, value))
        else:
            print("BAD... Expected {} {} but got no report of a validation failure".format(key, value))
            errors = errors + 1

    if errors:
        print("FAIL... {} out of {}".format(errors, len(tests)))
        sys.exit(-1)
    else:
        print("SUCCESS... {} out of {}".format(len(tests), len(tests)))
        sys.exit(0)


def usage():
    print('Usage: folder2transfer.py --fileset [fileSet] or test')


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
        csv2mets = Csv2Mets(fileset)
        csv2mets.run()


if __name__ == '__main__':
    main(sys.argv[1:])
