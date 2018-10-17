#!/usr/bin/env python
#
# restructure.py
#
# Restructure a folder structure
import getopt
import sys


class RestructureFolder:
    type = None
    fileset = None

    def __init__(self, type, fileset):
        self.type = type
        self.fileset = fileset

    def run(self):
        if self.type == 'single':
            self.single()
        elif self.type == 'archive':
            self.archive()

    def single(self):
        return

    def archive(self):
        return


def usage():
    print('Usage: restructure.py --fileset [fileSet] --type [type]')


def main(argv):
    fileset = None
    type = 'default'

    try:
        opts, args = getopt.getopt(argv, 'f:t:h', ['fileset=', 'type=', 'help'])
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
        if opt in ('-t', '--type'):
            type = arg

    assert fileset
    restructure = RestructureFolder(type, fileset)
    restructure.run()


if __name__ == '__main__':
    main(sys.argv[1:])
