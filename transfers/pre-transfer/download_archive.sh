#!/bin/bash
#
# download_archive.sh
#
# Download an archive master files by objid  (compound ID or accession number) access_point token manifest
#
# Usage: download_archive.sh objid url access_point token metadata-file fileset

OBJID="$1"
BASE_URL="$2"
TOKEN="$3"
SOR_METADATA_FILE="$4"
FILESET="$5"

NA="10622"

if [ -z "$OBJID" ]
then
    echo "Need an object id. E.g.: 10622/ARCH12345.6."
    exit 1
fi

if [ -z "$TOKEN" ]
then
    echo "Expect token as the second argument."
    exit 1
fi

if [ -z "$SOR_METADATA_FILE" ]
then
    echo "Expect file as the third argument."
    exit 1
else
    if [ ! -f "$SOR_METADATA_FILE" ]
    then
        echo "File not found: ${SOR_METADATA_FILE}"
        exit 1
    fi
fi

ACCESSION_NUMBER="${NA}/${OBJID}"
fileset="${FILESET}/${ACCESSION_NUMBER}"
mkdir -p "$fileset/preservation"
mkdir -p "$fileset/metadata"

checksum_file="$fileset/metadata/checksum.md5"
identifiers_file="$fileset/metadata/identifiers.json"

file="${fileset}/tmp"
grep ",${ACCESSION_NUMBER}," "$SOR_METADATA_FILE" > "$file"
if [ -z "$(cat ${file})" ]
then
    echo "Nothing to do. No files found with ${ACCESSION_NUMBER}"
    exit 1
fi

echo "Download the files"
last=""
while read line
do
    # Line is for example:
    # 10622/38119312-0313-4CE5-8A23-5E90A5AB3291,f218ccaf7ec7b2365b20a85030f648d0,10622/ARCH00210.5353,77,image/tiff,26434700,ARCH00210_5353_0077.tif
    # PID md5 objid seq contenttype length filename
    IFS=, read pid md5_expect bulk seq content_type length filename <<< "$line"

    if [[ "$filename" == "manifest.xml" ]]
    then
        continue
    fi

    extension="tif"
    if [[ "$content_type" == "image/jpeg" ]] || [[ "$content_type" == "image/jpg" ]]
    then
        extension="jpg"
    fi
    if [[ "$content_type" == "application/xml" ]] || [[ "$content_type" == "text/xml" ]]
    then
        extension="xml"
    fi

    url="${BASE_URL}/file/master/${pid}"
    seq="00000${seq}"
    seq="${seq:(-5)}"
    filename="${OBJID}_${seq}.${extension}"
    master_file="${fileset}/preservation/${filename}"
    wget --header="Authorization: Bearer ${TOKEN}" --no-check-certificate -O "$master_file" "$url"
    rc=$?
    if [ "$rc" == 0 ]
    then
#        Calculate a checksum
#        md5_actual=$(md5sum "$filename" | cut -d ' ' -f 1)
#        if [[ "$md5_actual" == "$md5_expect" ]]
#        then
#            echo "OK... ${pid} -> ${filename}"
#        else
#            echo "BAD... md5 mismatch. Expecting ${md5_expect} but got ${md5_actual} for ${pid} -> ${filename}"
#            report=1
#        fi
        echo "OK... ${pid} -> ${filename}"
        last="$filename"


    else
        echo "BAD... error ${rc} when downloading ${pid} -> ${filename}"
        report=1
        rm "$master_file"

    fi
done < "$file"


# Add our METS description
echo "Create the IISH METS file"
python mets.py --fileset="$fileset"


# Create the md5sum file
echo "Create the md5sum file"
while read line
do
    IFS=, read pid md5_expect bulk seq content_type length filename <<< "$line"

    if [[ "$filename" == "manifest.xml" ]]
    then
        continue
    fi

    seq="00000${seq}"
    seq="${seq:(-5)}"
    filename="${OBJID}_${seq}.${extension}"
    master_file="preservation/${filename}"


    echo "${md5_expect}  ${master_file}" >> "$checksum_file"
done < "$file"


# Create the identifier json file
echo "Create the identifier file"
echo "[" > "$identifiers_file"
while read line
do
    IFS=, read pid md5_expect bulk seq content_type length filename <<< "$line"

    if [[ "$filename" == "manifest.xml" ]]
    then
        continue
    fi

    seq="00000${seq}"
    seq="${seq:(-5)}"
    filename="${OBJID}_${seq}.${extension}"
    master_file="preservation/${filename}"


    echo "{
    \"file\": \"${master_file}\",
    \"identifiers\": [
      {
        \"identifier\": \"https://hdl.handle.net/${pid}\",
        \"identiferType\": \"URL\"
      },
      {
        \"identifier\": \"hdl:${pid}\",
        \"identiferType\": \"HANDLE\"
      }
    ]
  }" >> "$identifiers_file"

    if [[ "$filename" == "$last" ]]
    then
        echo "]" >> "$identifiers_file"
    else
        echo "," >> "$identifiers_file"
    fi

done < "$file"


rm "$file"

if [ "$report" == 0 ]
then
    echo "There were ${report} errors."
    exit 1
else
    echo "All OK"
    exit 0
fi