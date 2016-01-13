#!/usr/bin/env bash

function helptext {
    echo "Extract reads from a fastq.gz file by barcode"
    echo "-f    Fastq.gz file"
    echo "-b    Barcode sequence (e.g. ATCGNA)"
    echo "-o    Append output to outfile.gz (will create if it doesn't exist)"
    echo "-h    This help message"
}

[[ $# -gt 0 ]] || { helptext; exit 1; }

while getopts ":f:b:o:h" opt; do
    case $opt in
        f)
            FASTQ=$OPTARG
            ;;
        b)
            BARCODE=$OPTARG
            ;;
        o)
            OUTFILE=$OPTARG
            ;;
        h)
            helptext >&2
            exit 0
            ;;
        \?)
            echo "Invalid option specified: ${OPTARG}"
            helptext >&2
            exit 1
            ;;
    esac
done

zcat ${FASTQ} | grep -A 3 ":N:0:${BARCODE}$" | grep -v "\-\-" | gzip -c >> ${OUTFILE}

