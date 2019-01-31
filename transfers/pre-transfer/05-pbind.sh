#!/bin/bash
#
# Build transfer
#
# Prepare the mets, json and checksums for the package.
#
# Ensure the folder is structured correctly with validate.py
# Example: ./build_transfer.sh "10622/ARCH00842.1"
#
# 10622
# ├── ARCH00842.1
# │   └── preservation
# │       ├── ARCH00842.1_0001.tif
# │       └── ARCH00842.1_0002.tif

set -e

WORK="pbind"
source 01-settings.sh "$WORK"


function main {
    for fileset in "${FILESETS}/${WORK}/"*
    do
        if [[ -d "$fileset" ]]
        then
            archival_id=$(basename "$fileset")
            item_id=${archival_id#*.}
            echo "Found ${fileset}"
            queued "$fileset" "$WORK"
            if [[ "$?" == 0 ]]
            then
                identifiers_file="${FILESETS}/${archival_id}/metadata/identifiers.json"
                if [[ -f "$identifiers_file" ]]
                then
                    # Bind the archive as a whole
                    soapenv="<?xml version='1.0' encoding='UTF-8'?>  \
            <soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' xmlns:pid='http://pid.socialhistoryservices.org/'>  \
                <soapenv:Body> \
                    <pid:UpsertPidRequest> \
                        <pid:na>${NA}</pid:na> \
                        <pid:handle> \
                            <pid:pid>${NA}/${archival_id}</pid:pid> \
                            <pid:locAtt> \
                              <pid:location href='${CATALOG_URL}/Record/${archival_id}/ArchiveContentList#${item_id}' weight='1'/>
                              <pid:location href='${CATALOG_URL}/Record/${archival_id}/ArchiveContentList#${item_id}' weight='0' view='catalog'/>
                              <pid:location href='${url}/metadata/mets.xml' weight='0' view='mets'/>
                              <pid:location href='${url}/preservation/${archival_id}_0001.tif' weight='0' view='master'/>
                              <pid:location href='${url}/access/preservation/${archival_id}_0001.jpg' weight='0' view='level1'/>
                              <pid:location href='${url}/access/preservation/${archival_id}_0001.jpg' weight='0' view='level2'/>
                              <pid:location href='${url}/access/thumbnail/${archival_id}_0001.jpg' weight='0' view='level3'/>
                            </pid:locAtt> \
                        </pid:handle> \
                    </pid:UpsertPidRequest> \
                </soapenv:Body> \
            </soapenv:Envelope>"

                    # Next bind the pids as a whole
                    pids=$(/usr/bin/jq ".[].identifiers[].identifier")
                    for pid in "${pids}"
                    do

                    done
                else
                    sendmail "File not found" "Could not find ${identifiers_file}"
                    continue
                fi
            fi
        else
            echo "Ignoring file ${fileset}"
        fi
    done
}

main

exit 0