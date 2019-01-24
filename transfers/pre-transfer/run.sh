#!/bin/bash
#
# run.sh
# Validate the package and build the transfer

DIRNAME=`dirname "$0"`
if [[ -z "$DIRNAME" ]]
then
    DIRNAME=$(pwd)
fi

FILESET="$1"

"${DIRNAME}/../../work/virtualenv/bin/python2" "${DIRNAME}/validate.py" --fileset="$FILESET"
rc=$?
if [[ "$rc" == 0 ]]
then
    echo "The package is well formed."
else
    echo "The package is not well structured."
    exit "$rc"
fi

"${DIRNAME}/build_transfer.sh" "$FILESET"
rc=$?
if [[ "$rc" == 0 ]]
then
    echo "The package is build."
else
    echo "Unable to build the package."
    exit "$rc"
fi



exit 0