#!/bin/bash
#
# run.sh
# Start the flow
#
# Expected filesystem structure
# /
#  ├── stage
#  ├── fail
#  ├── validate
#  └── ready
#
# 1. The archivist will move approved packages into the stage folder.
# 2. The system will move the approved package into the validate folder.
# 3. The system will validate the package.
# 4. The system will move invalid packages into the fail folder.
# 5. The system will move valid packages into the ready folder.
#
# Assumptions:
# - the stage, fail and validate folders live on the same filesystem.
# - the AM storage service configuration is placed in  /etc/default/archivematica-storage-service

WORK="stage"
source 01-settings.sh "$WORK"

function main {
    for fileset in "${FILESETS}/${WORK}/"*
    do
        if [[ -d "$fileset" ]]
        then
            echo "Found ${fileset}"
            queued "$fileset" "$WORK"
            if [[ "$?" == 0 ]]
            then
                log "Move to validate" "Move ${fileset} to validate folder"
                mv "$fileset" "${FILESETS}/validate/"
            fi

        else
            echo "Ignoring file ${fileset}"
        fi
    done
}

main

exit 0