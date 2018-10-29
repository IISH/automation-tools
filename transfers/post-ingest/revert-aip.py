import os
import re
import sys
import time
import shutil
import datetime
import argparse
import subprocess
import dateutil.parser
from xml.etree import ElementTree

fitsNS = "http://hul.harvard.edu/ois/xml/ns/fits/fits_output"
mediaInfoNS = "https://mediaarea.net/mediainfo"
metsNS = "http://www.loc.gov/METS/"
premisNS = "info:lc/xmlns/premis-v2"
premisV3NS = "http://www.loc.gov/premis/v3"
xlinkNS = "http://www.w3.org/1999/xlink"
systemNS = "http://ns.exiftool.ca/File/System/1.0/"

fitsBNS = "{" + fitsNS + "}"
mediaInfoBNS = "{" + mediaInfoNS + "}"
metsBNS = "{" + metsNS + "}"
premisBNS = "{" + premisNS + "}"
premisV3BNS = "{" + premisV3NS + "}"
xlinkBNS = "{" + xlinkNS + "}"
systemBNS = "{" + systemNS + "}"

NSMAP = {
    'fits': fitsNS,
    'mediainfo': mediaInfoNS,
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
                .replace('%SIPDirectory%objects/', '') \
                .replace('%SIPDirectory%data/', '') \
                .replace('%transferDirectory%objects/', '') \
                .replace('%transferDirectory%data/', '')
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
                .replace('%transferDirectory%objects/', '') \
                .replace('%transferDirectory%data/', '')

            aip_file_path = os.path.join(self.__aip_location, file_path)
            reverted_file_path = os.path.join(self.__reverted_location, new_file)
            shutil.copyfile(aip_file_path, reverted_file_path)

            object_characteristics = premis_node.find('premis:objectCharacteristics', namespaces=NSMAP)
            dates = self.__find_access_and_modification_dates(object_characteristics, aip_file_path)
            os.utime(reverted_file_path, dates)

    def __find_access_and_modification_dates(self, object_characteristics, aip_file_path):
        access_date = None
        modify_date = None

        # First try the EXIF tool
        exif_access_date = object_characteristics.findtext('.//System:FileAccessDate', namespaces=NSMAP)
        if not exif_access_date:
            exif_access_date = object_characteristics.findtext('.//FileAccessDate', namespaces=NSMAP)

        exif_modify_date = object_characteristics.findtext('.//System:FileModifyDate', namespaces=NSMAP)
        if not exif_modify_date:
            exif_modify_date = object_characteristics.findtext('.//FileModifyDate', namespaces=NSMAP)

        # TODO: Dirty hack to make parsing easier
        if exif_access_date and exif_modify_date:
            n_exif_access_date = re.sub(r'([0-9]{4}):([0-9]{2}):([0-9]{2})', r'\g<1>/\g<2>/\g<3>', exif_access_date)
            n_exif_modify_date = re.sub(r'([0-9]{4}):([0-9]{2}):([0-9]{2})', r'\g<1>/\g<2>/\g<3>', exif_modify_date)

            n_exif_access_date = re.sub(r'([+\-])([0-9]{2}):([0-9]{2})', r'\g<1>\g<2>\g<3>', n_exif_access_date)
            n_exif_modify_date = re.sub(r'([+\-])([0-9]{2}):([0-9]{2})', r'\g<1>\g<2>\g<3>', n_exif_modify_date)

            access_date = time.mktime(dateutil.parser.parse(n_exif_access_date).timetuple())
            modify_date = time.mktime(dateutil.parser.parse(n_exif_modify_date).timetuple())

        # Then try the FITS tool
        if not modify_date:
            fits_modify_date = object_characteristics.findtext('.//fits:fileinfo/fits:fslastmodified', namespaces=NSMAP)

            if fits_modify_date:
                modify_date = int(fits_modify_date) // 1000

        # Then try the MediaInfo tool
        if not modify_date:
            mediainfo_modify_date = object_characteristics.findtext('.//mediainfo:File_Modified_Date', namespaces=NSMAP)
            if mediainfo_modify_date and mediainfo_modify_date.startswith('UTC'):
                mediainfo_modify_date = mediainfo_modify_date.replace('UTC ', '') + ' UTC'

            if mediainfo_modify_date:
                modify_date = time.mktime(dateutil.parser.parse(mediainfo_modify_date).timetuple())

        # Also obtain date from the AIP file
        file_access_date = int(os.path.getatime(aip_file_path))
        file_modify_date = int(os.path.getmtime(aip_file_path))

        self.__print_dates(aip_file_path, modify_date, file_modify_date)

        return (
            access_date if access_date else file_access_date,
            modify_date if modify_date else file_modify_date
        )

    def __find_in_physical_structmap(self, parents):
        elem = self.__physical_structmap
        for label in parents:
            elem = elem.find('./mets:div[@LABEL="' + label + '"]', namespaces=NSMAP)
        return elem

    @staticmethod
    def __print_dates(aip_file_path, modify_date, file_modify_date):
        if modify_date:
            modify_date_str = str(datetime.datetime.utcfromtimestamp(modify_date))
            file_modify_date_str = str(datetime.datetime.utcfromtimestamp(file_modify_date))

            if modify_date_str != file_modify_date_str:
                print(aip_file_path)
                print('Modify date: ' + file_modify_date_str + ' vs. METS ' + modify_date_str)


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
            print('The following files are missing: \n' + '\n'.join(files_missing) + '\n')

        if len(files_timestamp_difference) > 0:
            error = True
            print('The following files have a different timestamp: \n' + '\n'.join(files_timestamp_difference) + '\n')

        if len(files_checksum_difference) > 0:
            error = True
            print('The following files have different content: \n' + '\n'.join(files_checksum_difference) + '\n')

        return error

    def __run_rsync(self, options):
        command = 'rsync ' + options + ' ' \
                  + self.__original_location + '/ ' \
                  + self.__reverted_location
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()

        files = set()
        for path in output.splitlines()[1:-3]:
            if path.startswith('deleting '):
                path = path.replace('deleting ', '')

            is_unneeded_file = os.path.basename(path) in {'Thumbs.db', 'Icon', 'Icon\r', '.DS_Store'}
            all_hidden = [part_of_path for part_of_path in path.split('/') if part_of_path.startswith('.')]
            if not is_unneeded_file and not all_hidden:
                files.add(path)

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

    print('')

    comparer = Comparer(args.original, args.reverted)
    if comparer.compare():
        sys.exit(1)
