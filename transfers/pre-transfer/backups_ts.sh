#!/bin/bash
#
# backups_ts [source]
#
# Description:
# A simple copy script where src folders are gathered for copy actions

# exit on error
set -e

DATESTAMP=$(date +"%Y-%m-%dT%H.%M.%S")
LOG="/opt/backups_ts_${DATESTAMP}.log"

src="$1"
if [ -z "$src" ]
then
    echo -e "Need a source directory."
fi

if [ ! -d "$src" ]
then
    echo -e "${src} is not a directory."
fi

dest="$2"
if [ -z "$dest" ]
then
    echo -e "Need a destination directory"
fi

# errors are captured within the child script.
set +e

mgs=""
for folder in "$src"
do
    if [ -d "$folder" ]
    then
        ./backup_ts.sh "$folder" "$dest" > "$LOG"
        rc=$?
        if [[ $rc != 0 ]]
        then
            msg="Error copying ${src} to ${dest} by $(whoami)@$(/bin/hostname --fqdn):${0}. See log at ${LOG}"
        fi
    fi
done

if [ -z "$msg" ]
then
    echo "OK...">>"$LOG"
else
    python sendmail.py \
      --body="$msg" \
      --from="$MAIL_FROM" \
      --to="$MAIL_TO" \
      --subject="Backup error" \
      --mail_relay="MAIL_HOST" \
      --mail_user="MAIL_USER" \
      --mail_password="$MAIL_PASSWORD" >> "$LOG"
    echo "Bad... there were errors. A mail was send...">>"$LOG"
fi