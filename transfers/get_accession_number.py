#!/usr/bin/env python
"""
A PID has format: hdl:n1/n2.n3
A. hdl prefix
B. Colon
C. naming authority
D. Forward slash
E. Archival id with format ARCH|COLL number
F. A dot
C. Unit id (starting with 'dig') with format string

An accession number is however only expressed as the id part of the PID:
n2.n3

. E.g. given PID: hdl:12345/ARCH67890.dig123
then all these conventions result in a valid accession number: ARCH67890.dig123
folder1 + folder2:                    /a/b/c/d/e/f/12345/ARCH67890.dig123
folder1 + folder2 +   folder3:        /a/b/c/d/e/f/12345/ARCH67890/dig123
folder1 + folder2 +   filepart1:      /a/b/c/d/e/f/12345/ARCH67890/dig123.zip
folder1 + filepart1 + filepart2:      /a/b/c/d/e/f/12345/ARCH67890.dig123.zip
folder1 + folder2 +   file:           /a/b/c/d/e/f/12345/ARCH67890.dig123/*.zip
folder1 + folder2 +   folder3 + file: /a/b/c/d/e/f/12345/ARCH67890/dig123/*.zip

Folder structure always has precedence over filename.
"""
from __future__ import print_function
import re

PATTERN_PID = re.compile('(ARCH|COLL)[\d]{5}\.dig[\d]+$')


def get_pid(pid):
    return pid if PATTERN_PID.match(pid) else None


def parse_foldername(dirname):
    d = ('#/#/#/' + dirname).rsplit('/', 3)
    d[-1] = d[-1][:-4] if d[-1].endswith('.zip') else d[-1]
    return d


def parse_fs(dirname):
    d = parse_foldername(dirname)
    return get_pid(d[-2] + '.' + d[-1]) or \
           get_pid(d[-1]) or \
           get_pid(d[-3] + '.' + d[-2]) or \
           get_pid(d[-2])


def parse_value(text):
    text = text.replace('/', '.')
    return get_pid(text)


def parse(dirname):
    return parse_value(dirname) or parse_fs(dirname)