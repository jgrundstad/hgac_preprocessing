#!/bin/bash
JAVA=/home/jgrundst/jdk1.7.0_45/bin/java
FASTQC=/home/jgrundst/FastQC/bin/fastqc

function helptext {
	echo "-r	readgroup"
	echo "-h	this message"
	exit 0
}

[[ $# -gt 0 ]] || { helptext; }

while getopts "r:o:h" opt; do
	case $opt in
		r)
			READGROUP=$OPTARG
			;;
		h)
			helptext >&2
			;;
		\?)
			echo "Invalid option specified."
			helptext >&2
			exit 1;
			;;
	esac
done

V=$($JAVA -version 2>&1)
echo "JAVA version:"
echo $V

echo $READGROUP
$FASTQC -j $JAVA -o ../QC/ $READGROUP*txt.gz


