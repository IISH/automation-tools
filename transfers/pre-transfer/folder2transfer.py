#!/usr/bin/env python
#
# folder2transfer.py
#
# Restructure a folder to an Archivematica transfer
import getopt
import sys
import os
import shutil

from validate import ValidateFolder
from restructure import RestructureFolder
from mets import CreateMETS


def usage():
    print(
        'Usage: folder2transfer.py --hot [hot folder] --work [work folder] --ready [ready folder] --failed [failed folder]')


def main(argv):
    hot = None
    work = None
    ready = None
    failed = None

    try:
        opts, args = getopt.getopt(argv, 'h:w:r:f', ['hot=', 'work=', 'ready=', 'failed=', 'help'])
    except getopt.GetoptError as e:
        print("Opt error: " + e.msg)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '--help':
            usage()
            sys.exit()
        if opt in ('-h', '--hot'):
            hot = arg
        if opt in ('-w', '--work'):
            work = arg
        if opt in ('-r', '--ready'):
            ready = arg
        if opt in ('-f', '--failed'):
            failed = arg

    assert hot
    assert work
    assert ready
    assert failed

    for item in os.listdir(hot):
        validate = ValidateFolder(hot + '/' + item)
        validate.run()

        if validate.report['error']:
            shutil.copy(hot + '/' + item, failed)
        else:
            shutil.move(hot + '/' + item, work)

    for item in os.listdir(work):
        restructure = RestructureFolder('default', work + '/' + item)
        restructure.run()

    for item in os.listdir(work):
        mets = CreateMETS(work + '/' + item)
        mets.run()

    for item in os.listdir(work):
        shutil.move(work + '/' + item, ready)


if __name__ == '__main__':
    main(sys.argv[1:])
