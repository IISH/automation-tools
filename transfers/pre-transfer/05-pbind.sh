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

function clean {
    fileset="$1"
    for file in "${fileset}/"*
    do
        if [[ -f "$file" ]]
        then
            rm "$file"
        fi
    done
}


function bind_pid {
    soapenv="$1"
    echo "Binding ${PID_WEBSERVICE_ENDPOINT}:${PID_WEBSERVICE_KEY} ${soapenv}"
    wget -O /dev/null --header="Content-Type: text/xml" \
        --header="Authorization: oauth ${PID_WEBSERVICE_KEY}" \
        --post-data "$soapenv" \
        --no-check-certificate \
        "$PID_WEBSERVICE_ENDPOINT"
}


function main {
    for fileset in "${FILESETS}/${WORK}/"*
    do
        if [[ -d "$fileset" ]]
        then
            echo "Found ${fileset}"
            clean "$fileset"

            archival_id=$(basename "$fileset")
            main_archive=${archival_id%.*}
            item_id=${archival_id#*.}

            # Download the manifest
            manifest_json="${fileset}/manifest.json"
            set +e
            wget "${IIIF_SERVICE}/iiif/presentation/${archival_id}/manifest" -O "$manifest_json"
            rc=$?
            if [[ "$rc" == 0 ]] && [[ -f "$manifest_json" ]]
            then
                echo "Ok"
            else
                echo "Unable to download manifest. Skipping..."
                continue
            fi
            set -e

            # Determine the type of package...
            #   Image
            #   Sound
            #   Video
            #   Text
            #   Dataset
            package_id=""
            package_type=""
            see_also=$(/usr/bin/jq ".seeAlso" "$manifest_json")
            if [[ "$see_also" == "null" ]]
            then
                echo "Warning. No seeAlso field found. Is the file registered?"
            else
                package_id=$(/usr/bin/jq ".seeAlso[].id" "$manifest_json" | tr -d '"')
                package_type=$(/usr/bin/jq ".seeAlso[].profile" "$manifest_json" | tr -d '"')
            fi

            # Arrange the files by their type and url
            manifest_items="${fileset}/items.csv"
            for item in $(/usr/bin/jq ".items[].items[].items[].body|[.type,.id]|tostring" "$manifest_json")
            do
                echo "$item" | tr -d "\"\\\\[]" >> "$manifest_items"
            done

            # Where ever possible the last of the first two pids as representation of the entire archive.
            representation_url=""
            sample=$(head -n 2 "$manifest_items" | tail -n 1) # e.g. "Image https://dip-acc.iisg.amsterdam/iiif/image/7FCE8868-24A2-11E9-9E80-0CC47A477CAC/full/full/0/default.jpg"
            IFS="," read t id <<< "$sample"
            if [[ "$t" == "Image" ]]
            then
                base_url=${id%/full/*}  # e.g. "https://dip-acc.iisg.amsterdam/iiif/image/7FC3153C-24A2-11E9-B8DC-0CC47A477CAC/full"
                representation_url="<pid:location href='${base_url}/full/0/default.jpg' weight='0' view='level1'/>
                                    <pid:location href='${base_url}/!1500,1500/0/default.jpg' weight='0' view='level2'/>
                                    <pid:location href='${base_url}/!450,450/0/default.jpg' weight='0' view='level3'/>"
            fi

            # Bind the archive or item as a whole.
            catalog=""
            oai_metadata_prefix=""
            if [[ "$package_type" == "http://www.loc.gov/ead/ead.xsd" ]]
            then
                oai_metadata_prefix="ead"
                catalog="<pid:location href='${CATALOG_URL}/Record/${main_archive}/ArchiveContentList#${item_id}' weight='1'/>
                         <pid:location href='${CATALOG_URL}/Record/${main_archive}/ArchiveContentList#${item_id}' weight='0' view='catalog'/>"
            else
                oai_metadata_prefix="marc"
                catalog="<pid:location href='${CATALOG_URL}/Record/${main_archive}' weight='1'/>
                         <pid:location href='${CATALOG_URL}/Record/${main_archive}' weight='0' view='catalog'/>"
            fi

            if [[ ! -z "$package_id" ]]
            then
                catalog="${catalog}<pid:location weight='0' href='${package_id//&/&amp;}' view='${oai_metadata_prefix}'/>"
            fi

            soapenv="<?xml version='1.0' encoding='UTF-8'?>  \
            <soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' xmlns:pid='http://pid.socialhistoryservices.org/'>  \
                <soapenv:Body> \
                    <pid:UpsertPidRequest> \
                        <pid:na>${NA}</pid:na> \
                        <pid:handle> \
                            <pid:pid>${NA}/${archival_id}</pid:pid> \
                            <pid:locAtt> \
                              ${catalog}
                              <pid:location href='${IIIF_SERVICE}/iiif/presentation/${archival_id}/manifest' weight='0' view='manifest'/>
                              ${representation_url}
                            </pid:locAtt> \
                        </pid:handle> \
                    </pid:UpsertPidRequest> \
                </soapenv:Body> \
            </soapenv:Envelope>"

            bind_pid "$soapenv"

            # Next bind the pids as a whole
            while read line
            do
                IFS="," read t id <<< "$line"
                if [[ "$t" == "Image" ]]
                then
                    base_url=${id%/full/*}  # e.g. "https://dip-acc.iisg.amsterdam/iiif/image/7FC3153C-24A2-11E9-B8DC-0CC47A477CAC/full"
                    base_url=$(dirname "$base_url")  # e.g. "https://dip-acc.iisg.amsterdam/iiif/image/7FC3153C-24A2-11E9-B8DC-0CC47A477CAC"
                    id=$(basename "$base_url") # e.g. 7FC3153C-24A2-11E9-B8DC-0CC47A477CAC
                    soapenv="<?xml version='1.0' encoding='UTF-8'?>  \
                    <soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' xmlns:pid='http://pid.socialhistoryservices.org/'>  \
                        <soapenv:Body> \
                            <pid:UpsertPidRequest> \
                                <pid:na>${NA}</pid:na> \
                                <pid:handle> \
                                    <pid:pid>${NA}/${id}</pid:pid> \
                                    <pid:locAtt> \
                                      <pid:location href='${base_url}/info.json' weight='1'/>
                                      <pid:location href='${base_url}/info.json' weight='0' view='manifest'/>
                                      <pid:location href='${base_url}/full/full/0/default.jpg' weight='0' view='level1'/>
                                      <pid:location href='${base_url}/full/!1500,1500/0/default.jpg' weight='0' view='level2'/>
                                      <pid:location href='${base_url}/full/!450,450/0/default.jpg' weight='0' view='level3'/>
                                    </pid:locAtt> \
                                </pid:handle> \
                            </pid:UpsertPidRequest> \
                        </soapenv:Body> \
                    </soapenv:Envelope>"
                else
                    base_url=${id%/full/*}  # e.g. "https://dip-acc.iisg.amsterdam/iiif/image/7FC3153C-24A2-11E9-B8DC-0CC47A477CAC/full"
                    base_url=$(dirname "$base_url")  # e.g. "https://dip-acc.iisg.amsterdam/iiif/image/7FC3153C-24A2-11E9-B8DC-0CC47A477CAC"
                    id=$(basename "$base_url") # e.g. 7FC3153C-24A2-11E9-B8DC-0CC47A477CAC
                    soapenv="<?xml version='1.0' encoding='UTF-8'?>  \
                    <soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/' xmlns:pid='http://pid.socialhistoryservices.org/'>  \
                        <soapenv:Body> \
                            <pid:UpsertPidRequest> \
                                <pid:na>${NA}</pid:na> \
                                <pid:handle> \
                                    <pid:pid>${NA}/${id}</pid:pid> \
                                    <pid:locAtt> \
                                      <pid:location href='${base_url}/info.json' weight='1'/>
                                      <pid:location href='${base_url}/info.json' weight='0' view='manifest'/>
                                      <pid:location href='${base_url}/full/full/0/default.jpg' weight='0' view='level1'/>
                                      <pid:location href='${base_url}/full/!1500,1500/0/default.jpg' weight='0' view='level2'/>
                                      <pid:location href='${base_url}/full/!450,450/0/default.jpg' weight='0' view='level3'/>
                                    </pid:locAtt> \
                                </pid:handle> \
                            </pid:UpsertPidRequest> \
                        </soapenv:Body> \
                    </soapenv:Envelope>"
                fi
            bind_pid "$soapenv"
            done < "$manifest_items"

            log "Ready binding pids" "Bound pids for ${fileset}"
            rm -rf "$fileset"
        else
            echo "Ignoring file ${fileset}"
        fi
    done
}

main

exit 0