#!/usr/bin/env python
# coding=utf-8
#
# folder2csv.py [FILESET]
#
# Creates a CSV based on the folder structure.
#
# naming authority
#  [ARCHIVAL INVENTORY].[NUMBER]/[GROUP (unique and repeatable)]/[ARCHIVAL INVENTORY].[NUMBER]_[SEQUENCE].[EXTENSION]
#
# Example: folder2csv.py "10622/ARCH00842.1"
# 10622
# ├── ARCH00842.1
# │   └── preservation
# │       ├── ARCH00842.1_0001.tif
# │       └── ARCH00842.1_0002.tif
#
# Run validate.py [FILESET] to ensure this folder structure conforms to the above convention.

import getopt
import os
import sys
from preservation import Preservation
from error import Error
import re


class CreateCsv:
    fileset = None

    def __init__(self, fileset):
        self.fileset = fileset

    def run(self):
        accession_id = os.path.basename(self.fileset)
        print("Accession ID = " + accession_id)

        groups = [directory for directory in os.listdir(self.fileset) if os.path.isdir(self.fileset + '/' + directory)]
        for group in groups:



def usage():
    print('Usage: folder2csv.py --fileset [fileSet] or test')


def main(argv):
    fileset = None

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

    assert fileset
    CreateCsv(fileset).run()


if __name__ == '__main__':
    main(sys.argv[1:])
