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

WORK="build"
source 01-settings.sh "$WORK"

FILESET=""
METADATA_FOLDER="metadata"
ACCESS_COPIES_FOLDER="access"
ACCESSION_NUMBER=""
f=0

function add_group {
    group="$1"
    f=0
    for system in ${ACCESS_COPIES_FOLDER} ${METADATA_FOLDER}
    do
        if [[ "$group" == "$system" ]]
        then
            f=1
            break
        fi
    done
}

function checksums {
    file_checksum="${METADATA_FOLDER}/checksum.md5"
    echo "Building checksum ${file_checksum}"
    for group in *
    do
        add_group "$group"
        if [[ -d "$group" ]] && [[ "$f" == 0 ]]
        then
            /usr/bin/md5sum "$group"/* >> "$file_checksum"
        fi
    done

    # special case for access copies
    for group in "${ACCESS_COPIES_FOLDER}/"*
    do
        if [[ -d "$group" ]]
        then
            /usr/bin/md5sum "$group"/* >> "$file_checksum"
        fi
    done
}

function identifiers {

    identifiers_file="${METADATA_FOLDER}/identifiers.json"
    echo "Building identifiers ${identifiers_file}"
    last=""
    echo "[" > "$identifiers_file"
    for group in *
    do
        add_group "$group"
        if [[ -d "$group" ]] && [[ "$f" == 0 ]]
        then
            for file in "$group"/*
            do
                if [[ -z "$last" ]]
                then
                    last="1"
                else
                    echo "," >> "$identifiers_file"
                fi

                id=$(uuid)
                pid="${NA}/${id^^}"
                echo "{
    \"file\": \"${file}\",
    \"identifiers\": [
      {
        \"identifier\": \"https://hdl.handle.net/${pid}\",
        \"identiferType\": \"URI\"
      },
      {
        \"identifier\": \"${pid}\",
        \"identiferType\": \"hdl\"
      }
    ]
  }" >> "$identifiers_file"
            done
        fi
    done
    echo "]" >> "$identifiers_file"
}

function mets {
    fileset="$1"
    mets_file="${METADATA_FOLDER}/mets_structmap.xml"
    if [[ -f "$mets_file" ]]
    then
        echo "File exists ${mets_file}... delete this file if you want to recreate it"
        return
    fi

    echo "Building METS ${mets_file}"
    CMD="${PYTHON} \"${DIRNAME}/mets.py\" --fileset=\"${fileset}\""
    echo "$CMD"
    eval "${CMD}"
}

function main {
    for fileset in "${FILESETS}/${WORK}/"*
    do
        if [[ -d "$fileset" ]]
        then
            queued "$fileset" "$WORK"
            if [[ "$?" == 0 ]]
            then
                echo "Found ${fileset}"
                cd "$fileset"
                if [[ -d "${METADATA_FOLDER}" ]]
                then
                    rm -rf "${METADATA_FOLDER}"
                fi
                mkdir "${METADATA_FOLDER}"
                checksums
                identifiers
                mets "$fileset"
                chown -R archivematica:archivematica "$fileset"
                archival_id=$(basename "$fileset")

                # Mark that we want the PIDs
                mkdir -p "${FILESETS}/pbind/${archival_id}"

                # Move it to the ready folder
                log "Move to ready" "Move ${fileset} to ready folder"
                mv "$fileset" "${FILESETS}/ready/"
            fi
        else
            echo "Ignoring file ${fileset}"
        fi
    done
}

main
