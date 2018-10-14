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
import csv
import getopt
import os
import sys
from preservation import Preservation
from error import Error


def normalize(items):
    """Only accept alphabetical and underscores headers, that are defined in the header lists"""

    def alpha_or_underscore(text):
        return ''.join([c for c in str(text) if c.isalpha() or c is '_'])

    items = map(alpha_or_underscore, map(str.lower, map(str.strip, items)))
    return [item for item in items if item]


def get_header(csvfile):
    header = None
    with open(csvfile, 'r') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for items in reader:
            header = normalize(items)
            break

    f.close()
    return header if header else []


def get_header_groups(headers):
    """ Retrieves the gruop file headers from the header"""
    return [item for item in headers if item in Preservation.FILE_GROUP]


def read_filegroup(csvfile):
    """Read in the filegroups from the CSV
    """
    header_groups = get_header(csvfile)
    file_groups = get_header_groups(header_groups)
    inventory_groups = []

    # Determine the inventory nunbers. This is a groupBy operation
    with open(csvfile, 'r') as f:
        f.readlines()  # ignore the header, as we already parsed it.
        reader = csv.reader(f, delimiter=',', quotechar='"')
    f.close()


class Csv2Mets:
    fileset = None
    report = {'error': list(), 'info': list(), 'codes': list()}
    csv_index = {}

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
        print(str(code) + ':' + text)


    def run(self):
        accession_id = os.path.basename(self.fileset)

        self.info("Accession ID = " + accession_id)

        # --------------------------------------------------------------------------------------------------------------
        # validate 1: must have a manifest
        # --------------------------------------------------------------------------------------------------------------
        manifest_file = self.fileset + '/manifest.csv'
        if not os.path.exists(manifest_file):
            return self.error(Error.NO_MANIFEST, Error.NO_MANIFEST_MSG.format(manifest_file))

        folders = [directory for directory in os.listdir(self.fileset) if
                   os.path.isdir(self.fileset + '/' + directory)]

        # --------------------------------------------------------------------------------------------------------------
        # validate 2: a fileset cannot be empty
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
        # Validate 7: headers must be of a known file group or sys group
        # --------------------------------------------------------------------------------------------------------------
        csv_headers = get_header(manifest_file)
        for header in csv_headers:
            if header in Preservation.VALID_HEADERS or header in Preservation.FILE_GROUP:
                self.info("Header {} is known".format(header))
            else:
                self.error(Error.UNKNOWN_HEADER, Error.UNKNOWN_HEADER_MSG.format(header, Preservation))
        if self.report['error']:
            return

        # --------------------------------------------------------------------------------------------------------------
        # Validate 8: ensure no duplicate keys are part of the CSV
        # --------------------------------------------------------------------------------------------------------------
        for header in csv_headers:
            count = csv_headers.count(header)
            if csv_headers.count(header) > 1:
                self.error(Error.DUPLICATE_HEADER, Error.DUPLICATE_HEADER_MSG.format(count, header))
        if self.report['error']:
            return

        # --------------------------------------------------------------------------------------------------------------
        # Validate:
        # 4. The CSV must have a header
        # 5. All known fileGroups in the CSV must exists as a folder in the fileset;
        # 6. and vice versa.
        # --------------------------------------------------------------------------------------------------------------
        group_headers = get_header_groups(csv_headers)
        if group_headers:
            # validate 6
            for folder in folders:
                if folder in group_headers:
                    self.info("Found folder name {} in CSV header".format(folder))
                else:
                    self.error(Error.MISSING_HEADER_ITEM_FOR_EXISTING_FOLDER,
                               Error.NO_HEADER_ITEM_MSG.format(folder, manifest_file))
            # validate 5
            for head in group_headers:
                if head in folders:
                    self.info("Found CSV header key {} in folder".format(head))
                else:
                    self.error(Error.MISSING_FOLDER_NAME_FOR_EXISTING_HEADER,
                               Error.MISSING_FOLDER_NAME_FOR_EXISTING_HEADER_MSG.format(head, manifest_file))
        else:
            # validate 4
            self.error(Error.NO_HEADER,
                       Error.NO_HEADER_MSG.format(manifest_file))
        if self.report['error']:
            return

        # Create a index-key relationship so we can select the column later by name.
        for idx, header in enumerate(csv_headers):
            self.csv_index[header] = idx
            self.info("Map CSV index {}={}".format(idx, header))


def unit_tests():
    print('Run unit tests.')

    this_dir = os.path.abspath(os.path.dirname(__file__))
    tests = {'ARCH1': Error.NO_MANIFEST, 'ARCH2': Error.NO_GROUPS, 'ARCH3': Error.UNKNOWN_GROUPS,
             'ARCH4': Error.NO_HEADER, 'ARCH5': Error.MISSING_HEADER_ITEM_FOR_EXISTING_FOLDER,
             'ARCH6': Error.MISSING_FOLDER_NAME_FOR_EXISTING_HEADER, 'ARCH7': Error.UNKNOWN_HEADER,
             'ARCH8': Error.DUPLICATE_HEADER,
             'ARCH0': 0}
    errors = 0
    # noinspection PyCompatibility
    for key, value in tests.iteritems():
        csv2mets = Csv2Mets((this_dir + '/tests/' + key))
        csv2mets.run()
        if not value or value in csv2mets.report['codes']:
            print("OK... {} {} {}".format(key, value, csv2mets.report['error']))
        else:
            print("BAD... Expected {} {} but got no report of a validation failure".format(key, value))
            errors = errors + 1
        csv2mets.clear()

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
