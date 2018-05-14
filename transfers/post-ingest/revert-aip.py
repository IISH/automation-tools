import os
import re
import sys
import time
import shutil
import argparse
import subprocess
import dateutil.parser
from xml.etree import ElementTree

metsNS = "http://www.loc.gov/METS/"
premisNS = "info:lc/xmlns/premis-v2"
premisV3NS = "http://www.loc.gov/premis/v3"
xlinkNS = "http://www.w3.org/1999/xlink"
systemNS = "http://ns.exiftool.ca/File/System/1.0/"

metsBNS = "{" + metsNS + "}"
premisBNS = "{" + premisNS + "}"
premisV3BNS = "{" + premisV3NS + "}"
xlinkBNS = "{" + xlinkNS + "}"
systemBNS = "{" + systemNS + "}"

NSMAP = {
    'mets': metsNS,
    'premis': premisNS,
    'premisv3': premisV3NS,
    'xlink': xlinkNS,
    'System': systemNS,
}


class AipReverter:
    def __init__(self, aip_location, reverted_location):
        self.__aip_location = os.path.join(aip_location, 'data')
        self.__reverted_location = reverted_location

        mets_filename = [filename for filename in os.listdir(self.__aip_location) if
                         filename.startswith("METS") and filename.endswith(".xml")][0]
        mets_path = os.path.join(self.__aip_location, mets_filename)

        self.__tree = ElementTree.parse(mets_path)
        self.__physical_structmap = self.__tree.find('mets:structMap[@TYPE="physical"]/mets:div/mets:div',
                                                     namespaces=NSMAP)

    def revert_aip(self):
        cur_node = self.__tree.find('mets:structMap[@TYPE="logical"]/mets:div/mets:div', namespaces=NSMAP)
        self.__walk_tree(cur_node, [])

    def __walk_tree(self, cur_node, parents):
        for node in cur_node.findall('./mets:div', namespaces=NSMAP):
            if node.get('TYPE') == 'Directory':
                self.__restore_folder(node, parents)
                updated_parents = list(parents) + [node.get('LABEL')]
                self.__walk_tree(node, updated_parents)
            else:
                self.__restore_file(node, parents)

    def __restore_folder(self, node, parents):
        dmd_id = node.get('DMDID')
        if not dmd_id:
            label = node.get('LABEL')
            dmd_id = self.__find_in_physical_structmap(parents) \
                .find('./mets:div[@LABEL="' + label + '"]', namespaces=NSMAP) \
                .get('DMDID')

        if dmd_id:
            new_folder = self.__tree \
                .findtext('mets:dmdSec[@ID="' + dmd_id + '"]//premisv3:originalName', namespaces=NSMAP) \
                .replace('%SIPDirectory%objects/', '')
            os.makedirs(os.path.join(self.__reverted_location, new_folder))

    def __restore_file(self, node, parents):
        label = node.get('LABEL')
        file_id = self.__find_in_physical_structmap(parents) \
            .find('./mets:div[@LABEL="' + label + '"]/mets:fptr', namespaces=NSMAP) \
            .get('FILEID')

        file_node = self.__tree.find('mets:fileSec/mets:fileGrp[@USE="original"]/mets:file[@ID="' + file_id + '"]',
                                     namespaces=NSMAP)
        if file_node is not None:
            file_path = file_node.find('./mets:FLocat', namespaces=NSMAP).get(xlinkBNS + 'href')

            amd_id = file_node.get('ADMID')
            premis_node = self.__tree.find('mets:amdSec[@ID="' + amd_id + '"]/mets:techMD//premis:object',
                                           namespaces=NSMAP)
            new_file = premis_node \
                .findtext('premis:originalName', namespaces=NSMAP) \
                .replace('%transferDirectory%objects/', '')

            access_date = premis_node \
                .findtext('premis:objectCharacteristics//System:FileAccessDate', namespaces=NSMAP)
            if not access_date:
                access_date = premis_node \
                    .findtext('premis:objectCharacteristics//FileAccessDate', namespaces=NSMAP)

            modify_date = premis_node \
                .findtext('premis:objectCharacteristics//System:FileModifyDate', namespaces=NSMAP)
            if not modify_date:
                modify_date = premis_node \
                    .findtext('premis:objectCharacteristics//FileModifyDate', namespaces=NSMAP)

            aip_file_path = os.path.join(self.__aip_location, file_path)
            reverted_file_path = os.path.join(self.__reverted_location, new_file)
            shutil.copyfile(aip_file_path, reverted_file_path)

            # TODO: Dirty hack to make parsing easier
            access_date = re.sub(r'([0-9]{4}):([0-9]{2}):([0-9]{2})', r'\g<1>/\g<2>/\g<3>', access_date)
            modify_date = re.sub(r'([0-9]{4}):([0-9]{2}):([0-9]{2})', r'\g<1>/\g<2>/\g<3>', modify_date)

            os.utime(reverted_file_path, (
                time.mktime(dateutil.parser.parse(access_date).timetuple()),
                time.mktime(dateutil.parser.parse(modify_date).timetuple())
            ))

    def __find_in_physical_structmap(self, parents):
        elem = self.__physical_structmap
        for label in parents:
            elem = elem.find('./mets:div[@LABEL="' + label + '"]', namespaces=NSMAP)
        return elem


class Comparer:
    def __init__(self, original_location, reverted_location):
        self.__original_location = original_location
        self.__reverted_location = reverted_location

    def compare(self):
        error = False
        files_timestamp_difference = self.__run_rsync('-nvr --delete')
        files_checksum_difference = self.__run_rsync('-nvrc --delete')

        files_missing = files_timestamp_difference & files_checksum_difference
        files_timestamp_difference = files_timestamp_difference - files_missing
        files_checksum_difference = files_checksum_difference - files_missing

        if len(files_missing) > 0:
            error = True
            print('The following files are missing: \n' + '\n'.join(files_missing))

        if len(files_timestamp_difference) > 0:
            error = True
            print('The following files have a different timestamp: \n' + '\n'.join(files_timestamp_difference))

        if len(files_checksum_difference) > 0:
            error = True
            print('The following files have different content: \n' + '\n'.join(files_checksum_difference))

        return error

    def __run_rsync(self, options):
        command = 'rsync ' + options + ' ' \
                  + self.__original_location + '/ ' \
                  + self.__reverted_location
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()

        files = set(output.splitlines()[1:-3])
        files = files - {'Thumbs.db', 'Icon', 'Icon\r', '.DS_Store'}
        files = set([file for file in files if not file.startswith('.')])

        return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-a', '--aip', metavar='AIP', required=True, help='Path to the collection after ingest (AIP).')
    parser.add_argument('-o', '--original', metavar='ORIGINAL', required=True,
                        help='Path to the original collection before ingest.')
    parser.add_argument('-r', '--reverted', metavar='REVERTED', required=True,
                        help='The path to the location where the reverted AIP is stored.')

    args = parser.parse_args()

    aip_reverter = AipReverter(args.aip, args.reverted)
    aip_reverter.revert_aip()

    comparer = Comparer(args.original, args.reverted)
    if comparer.compare():
        sys.exit(1)
