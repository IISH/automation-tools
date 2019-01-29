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

DIRNAME=`dirname "$0"`
if [[ -z "$DIRNAME" ]]
then
    DIRNAME=$(pwd)
fi

FILESET=""
NA=10622 # This value could also be gotten from the parent folder of the fileset
METADATA="metadata"
PRESERVATION="preservation transcription"
ACCESSION_NUMBER=""
f=0

function add_group {
    group="$1"
    f=1
    for preserve in ${PRESERVATION}
    do
        if [[ "$group" == "$preserve" ]]
        then
            f=0
            break
        fi
    done
}

function checksums {
    file_checksum="${METADATA}/checksum.md5"
    if [[ -f "$file_checksum" ]]
    then
        echo "File exists ${file_checksum}... delete this file if you want to recreate it"
        return
    fi

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
    for group in "access/"*
    do
        /usr/bin/md5sum "$group"/* >> "$file_checksum"
    done
}

function identifiers {

    identifiers_file="${METADATA}/identifiers.json"
    if [[ -f "$identifiers_file" ]]
    then
        echo "File exists ${identifiers_file}... delete this file if you want to recreate it"
        return
    fi

    echo "Building identifiers ${identifiers_file}"
    last=""
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
}

function mets {
    mets_file="${METADATA}/mets_structmap.xml"
    if [[ -f "$mets_file" ]]
    then
        echo "File exists ${mets_file}... delete this file if you want to recreate it"
        return
    fi

    echo "Building METS ${mets_file}"

    "${DIRNAME}/../../work/virtualenv/bin/python2" "${DIRNAME}/mets.py" --fileset="$FILESET"
}

function main {
    FILESET="$1"
    if [[ -z "$FILESET" ]]
    then
        echo "Fileset cannot be empty".
        exit 1
    else
        if [[ ! -d "$FILESET" ]]
        then
            echo "No such directory: ${FILESET}".
            exit 1
        fi
    fi

    ACCESSION_NUMBER=${PWD##*/}

    cd "$FILESET"
    if [[ ! -d "$METADATA" ]]
    then
        mkdir "$METADATA"
    fi

    checksums
    identifiers
    mets
}

main "$@"
