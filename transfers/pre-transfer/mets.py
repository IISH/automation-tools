#!/usr/bin/env python
#
# mets.py
#
# Creates IISH METS for a folder structure
import os
import sys
import getopt
from xml.sax.saxutils import XMLGenerator
from preservation import Preservation

_attributes = {u'xmlns': 'http://www.loc.gov/METS/',
               u'xmlns:xlink': 'http://www.w3.org/1999/xlink',
               'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
               'xsi:schemaLocation': 'http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd'}


class MetsDocument:
    def __init__(self, output, encoding='utf-8', short_empty_elements=True):
        """
        Set up a document object, which takes SAX events and outputs
        an XML log file
        """
        document = XMLGenerator(output, encoding)  # Python 3.2 : short_empty_elements
        document.startDocument()
        self._document = document
        self._output = output
        self._encoding = encoding
        self._short_empty_elements = short_empty_elements
        self._open_elements = []
        return

    def close(self):
        """
        Clean up the logger object
        """
        self._document.endDocument()
        self._output.close()
        return

    def elem(self, element, attributes=None, characters=None):
        if not attributes:
            attributes = {}
        self._open_elements.append(element)
        self._document.startElement(element, attributes)
        if characters is not None:
            self._document.characters(characters)
        return self

    def close_entry(self, elements=1):
        for i in range(elements):
            element = self._open_elements.pop()
            self._document.endElement(element)
        return self


class CreateMETS:
    fileset = None
    manifest = None
    xl = None
    files = []

    def __init__(self, fileset):
        self.fileset = fileset

    def run(self):
        self.organize_files()

        if not os.path.exists(self.fileset + '/metadata'):
            os.makedirs(self.fileset + '/metadata')

        self.manifest = open(self.fileset + '/metadata/mets_structmap.xml', 'w')
        self.xl = MetsDocument(self.manifest)

        self.xl.elem(u'mets', _attributes)
        self.create_structmap()
        self.xl.close_entry().close()

    def organize_files(self):
        file_counter = 0

        for directory in os.listdir(self.fileset):
            if os.path.isdir(self.fileset + '/' + directory) and directory in Preservation.FILE_GROUP:
                for file in os.listdir(self.fileset + '/' + directory):
                    if os.path.isfile(self.fileset + '/' + directory + '/' + file):
                        file_counter += 1

                        file_ref = directory + '/' + file
                        file_seq = int(os.path.splitext(file)[0].split('_')[1])

                        self.files.append({
                            'ref': file_ref,
                            'seq': file_seq,
                            'group': directory
                        })

        self.files = sorted(self.files, key=lambda file: file['seq'])

    def create_structmap(self):
        self.xl.elem('structMap', {'ID': 'structMap_iish', 'TYPE': 'logical', 'LABEL': 'IISH structure'}).elem('div')

        last_seq = None
        for file in self.files:
            if not last_seq == file['seq']:
                if last_seq is not None:
                    self.xl.close_entry()
                last_seq = file['seq']
                self.xl.elem('div', {'LABEL': 'Page ' + str(file['seq']), 'ORDER': str(file['seq']), 'TYPE': 'page'})

            self.xl.elem('fptr', {'FILEID': file['ref']}).close_entry()

        self.xl.close_entry(3)


def usage():
    print('Usage: mets.py --fileset [fileSet]')


def main(argv):
    fileset = None

    try:
        opts, args = getopt.getopt(argv, 'f:h', ['fileset=', 'help'])
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

    assert fileset
    mets = CreateMETS(fileset)
    mets.run()


if __name__ == '__main__':
    main(sys.argv[1:])
