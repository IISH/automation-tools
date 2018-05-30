#!/bin/bash
#
# backup_ts [source] [target]
#
# Description:
# A simple copy script where files in one folder are transfered onto another folder.

# exit on error
set -e

src="$1"
if [ -z "$src" ]
then
    echo -e "Need a source directory."
fi

if [ ! -d "$src" ]
then
    echo "${src} is not a directory."
fi

dest="$2"
if [ -z "$dest" ]
then
    echo -e "Need a destination directory"
fi

echo "Copy request from ${src} to ${dest}"

FILE_STATUS="${dest}/.status"
if [ -f "$FILE_STATUS" ]
then
    echo "The destination folder has a ${FILE_STATUS} file and will be skipped. Remove this file to make a (new) transfer."
else
    /usr/bin/rsync -av --progress "$src" "$dest"
    echo "OK" > "$FILE_STATUS"
fi