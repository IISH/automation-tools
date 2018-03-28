#!/bin/bash
#-----------------------------------------------------------------------------------------------------------------------
# Validate the AIP and inform the acquisition database of its status.
#-----------------------------------------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------------------------------------
# Circuit stopper.
#-----------------------------------------------------------------------------------------------------------------------
self=$(basename "$0")
if (( $(pgrep -c "$self") == 1 ))
then
    echo "Self ${self}"
else
    echo "Already running"
    exit 0
fi


#-----------------------------------------------------------------------------------------------------------------------
# Task id codes
#-----------------------------------------------------------------------------------------------------------------------
AIP=70

#-----------------------------------------------------------------------------------------------------------------------
# Task status code
#-----------------------------------------------------------------------------------------------------------------------
FINISHED=3
FAILED=4

#-----------------------------------------------------------------------------------------------------------------------
# Naming authority
#-----------------------------------------------------------------------------------------------------------------------
NA="10622"

#-----------------------------------------------------------------------------------------------------------------------
# Acquisition database
#-----------------------------------------------------------------------------------------------------------------------
acquisition_database="https://digcolproc-acquisition.iisg.nl"
acquisition_database_access_token="$1"


#-----------------------------------------------------------------------------------------------------------------------
# Reference
#-----------------------------------------------------------------------------------------------------------------------
MINUTES="$2"


#-----------------------------------------------------------------------------------------------------------------------
# Storage service paths defaults
#-----------------------------------------------------------------------------------------------------------------------
AIP_LOCATION="/data/aip/10622/000"
SS_LOCATION="/data/aip/10622/storage_service"


#-----------------------------------------------------------------------------------------------------------------------
# call_api_status
# Use the API to sent status and message updates
#-----------------------------------------------------------------------------------------------------------------------
function call_api_status() {
    pid=$1
    status=$2
    subStatus=$3
    message="$4"

    if [ -z "$pid" ]; then
        echo "Error: pid argument is empty."
        exit 1
    fi
    if [ -z "$status" ]; then
        echo "Error: status argument is empty."
        exit 1
    fi
    if [ -z "$subStatus" ]; then
        echo "Error: subStatus argument is empty."
        exit 1
    fi

    # Update the status using the 'status' web service
    request_data="pid=${pid}&status=${status}&subStatus=${subStatus}&access_token=${acquisition_database_access_token}&message=${message}"
    endpoint="${acquisition_database}/service/status"
    rc=$(curl -o /dev/null -s --insecure --max-time 5 -w "%{http_code}" --data "$request_data" "$endpoint")
    if [[ "$rc" == 200 ]]
    then
        echo "OK... ${endpoint} ${request_data}"
    else
        echo "Error when contacting ${endpoint} got statuscode ${rc}"
        exit 1
    fi
    return 0
}


#-----------------------------------------------------------------------------------------------------------------------
# call_api_status
#-----------------------------------------------------------------------------------------------------------------------
v="/tmp/validate.txt"
find "$AIP_LOCATION" -mmin "$MINUTES" -name "*.7z" -type f > "$v"
while read line
do
    echo "$line"

    filename=$(basename "$line")
    uuid=$(echo "$filename" | cut -f 2-  -d "-" | cut -f 1 -d ".")
    id=$(echo "$filename" | cut -f 1  -d "-") # e.g. COLL00180.dig3385
    id="00000${id:13}" # e.g. 000003385
    id="${id: -5}" # e.g. 03385
    id="BULK${id}" # e.g. BULK03385
    folder="/tmp/${id}"
    pid="${NA}/${id}"
    status=""

    # Determine the pointer file
    size=${#AIP_LOCATION}
    path=$(dirname "$line")
    pointer_file="${SS_LOCATION}${path:size}/pointer.${uuid}.xml"

    # No need to repeat ourselves
    file_ok="/tmp/${uuid}"
    if [ -f "$file_ok" ]
    then
        "Skipping checks that already passed the test."
    else
        # Calculate the checksum
        echo "Verify by checksum"
        expected_message_digest=$(grep -oP '(?<=<premis:messageDigest>).*?(?=<)' "$pointer_file")
        actual_message_digest=$(/usr/bin/sha256sum "$line" | cut -d ' ' -f 1)
        if [[ "$expected_message_digest" == "$actual_message_digest" ]]
        then
            echo "Checksum match"
        else
            echo "Checksum mismatch ${line}. Expect ${expected_message_digest} but got ${actual_message_digest}"
            status="$FAILED"
            msg="Checksum mismatch"
        fi

        echo "Check for a removedFilesWithNoPremisMetadata event"
        7z e -o"$folder" "$line" removedFilesWithNoPremisMetadata.log -r
        if [ -f "${folder}/removedFilesWithNoPremisMetadata.log" ]
        then
            status="$FAILED"
            msg="Error!"
            cat "${folder}/removedFilesWithNoPremisMetadata.log"
            rm -r "$folder"
        fi
    fi

    if [ "$status" == "$FAILED" ]
    then
       echo "There were errors."
    else
        status="$FINISHED"
        msg="https://repository-storage-1.collections.iisg.org/api/v2/file/${uuid}/pointer_file/"
        touch "$file_ok"
    fi

    call_api_status "$pid" "$AIP" "$status" "$msg"

done < "$v"