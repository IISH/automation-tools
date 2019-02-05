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
                    # Bind the archive as a whole.
                    # Use the last of the first two pids as representation of the entire archive.
                    pid=$(/usr/bin/jq ".[].identifiers[].identifier" "$identifiers_file" | head  -n 4 | tail -n 1) # e.g. 10622/12345
                    id=$(basename "$pid") # e.g. 12345

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
                                      <pid:location weight='0' href='${OAI_SERVICE}?verb=GetRecord&amp;identifier=oai:socialhistoryservices.org:${pid}&amp;metadataPrefix=ead' view='ead'/>
                                      <pid:location href='${IIIF_SERVICE}/iiif/presentation/ARCH00822.4/manifest' weight='0' view='manifest'/>
                                      <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/full/full/0/default.jpg' weight='0' view='level1'/>
                                      <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/full/!1500,1500/0/default.jpg' weight='0' view='level2'/>
                                      <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/full/!450,450/0/default.jpg' weight='0' view='level3'/>
                                    </pid:locAtt> \
                                </pid:handle> \
                            </pid:UpsertPidRequest> \
                        </soapenv:Body> \
                    </soapenv:Envelope>"
            else
                echo "Ignoring file ${fileset}"
                continue
            fi

            # Next bind the pids as a whole
            pids=$(/usr/bin/jq ".[].identifiers[].identifier" "$identifiers_file")
            for pid in "${pids}"
            do
                id=$(basename "$pid") # e.g. 12345
                soapenv="<?xml version='1.0' encoding='UTF-8'?>  \
                <soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' xmlns:pid='http://pid.socialhistoryservices.org/'>  \
                    <soapenv:Body> \
                        <pid:UpsertPidRequest> \
                            <pid:na>${NA}</pid:na> \
                            <pid:handle> \
                                <pid:pid>${pid}</pid:pid> \
                                <pid:locAtt> \
                                  <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/info.json' weight='1'/>
                                  <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/info.json' weight='0' view='manifest'/>
                                  <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/full/full/0/default.jpg' weight='0' view='level1'/>
                                  <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/full/!1500,1500/0/default.jpg' weight='0' view='level2'/>
                                  <pid:location href='${IIIF_SERVICE}/iiif/image/${id}/full/!450,450/0/default.jpg' weight='0' view='level3'/>
                                </pid:locAtt> \
                            </pid:handle> \
                        </pid:UpsertPidRequest> \
                    </soapenv:Body> \
                </soapenv:Envelope>"
            done


                log "Move to ready" "Move ${fileset} to ready folder"
                mv "$fileset" "${FILESETS}/ready/"
            fi
        else
            echo "Ignoring file ${fileset}"
        fi
    done
}

main

exit 0