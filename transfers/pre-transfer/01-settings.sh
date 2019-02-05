#!/bin/bash

#-----------------------------------------------------------------------------------------------------------------------
# Settings global
#-----------------------------------------------------------------------------------------------------------------------
CATALOG_URL=""
DIRNAME=""
EMAIL_HOST_USER=""
EMAIL_HOST=""
EMAIL_TO=""
EMAIL_HOST_PASSWORD=""
FILESETS=""
IIIF_SERVICE=""
NA=""
OAI_SERVICE=""
PID_WEBSERVICE_KEY=""
PID_WEBSERVICE_ENDPOINT=""
PYTHON=""
SRU_SERVICE=""
WORK=""


#-----------------------------------------------------------------------------------------------------------------------
# load variables setup
#-----------------------------------------------------------------------------------------------------------------------
function setup {

    source /etc/default/archivematica-storage-service

    DIRNAME=$(pwd)

    if [[ ! -d "$FILESETS" ]] || [[ ! -d "${FILESETS}/${WORK}" ]]
    then
        echo "${FILESETS} or its subfolder ${WORK} is not a directory."
        exit 1
    fi

    PYTHON="${PYTHON}/bin/python2"
    if [[ ! -f "${PYTHON}" ]]
    then
        echo "Cannot find python virtual environment at ${PYTHON}"
        exit 1
    fi
}


#-----------------------------------------------------------------------------------------------------------------------
# utility log
#-----------------------------------------------------------------------------------------------------------------------
function log {
    subject="$1"
    body="$2"
    datestamp=$(date +"%Y-%m-%dT%H:%M:%S")
    echo "${datestamp}
${subject}
${body}"
}

#-----------------------------------------------------------------------------------------------------------------------
# utility sendmail
#-----------------------------------------------------------------------------------------------------------------------
function sendmail {
    subject="$1"
    body="$2"

    log "$subject" "$body"

    "$PYTHON" "${DIRNAME}/sendmail.py" \
        --body="Report from $(/bin/hostname --fqdn) ${body}" \
        --from="${EMAIL_HOST_USER}" \
        --to="${EMAIL_TO}" \
        --mail_relay="${EMAIL_HOST}" \
        --subject="${subject}" \
        --mail_user="${EMAIL_HOST_USER}" \
        --mail_password="${EMAIL_HOST_PASSWORD}"
}

#-----------------------------------------------------------------------------------------------------------------------
# singleton Circuit breaker.
# Stop if this script is already running in another thread.
#-----------------------------------------------------------------------------------------------------------------------
function singleton {
    self="${WORK}.sh"
    c=$(pgrep -c "$self")
    if [[ "$c" == 2 ]]
    then
        /bin/echo "Instantiating ${self}"
    else
        /bin/echo "Already running an instance of ${self}"
        exit 0
    fi
}


function queued {
    fileset="$1"
    work="$2"
    archival_id=$(basename "$fileset")
    for queue in build fail pbind ready stage validate
    do
        if [[ -d "${FILESETS}/${queue}/${archival_id}" ]]
        then
            if [[ "$queue" == "$work" ]]
            then
                continue
            else
                log "Staging error" "Fileset ${fileset} already exist in the ${queue} queue. Ignoring the folder."
                return 1
            fi
        fi
    done
    return 0
}


function init {
    WORK="$1"
    singleton
    setup
}

init "$@"