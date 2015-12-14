# hgac_preprocessing
Illumina preprocessing daemon

The hgac_preprocessing software relies on an HGAC SeqConfig web application service for
managing and performing Illumina bcl conversion and demultiplexing processes.
 
This repository contains 2 primary components:

1. ```HGAC_run_monitor.py``` - Watch the defined root data directory for completed sequencing runs,
and perform preprocessing as described by each run's parameters.
2. ```HGAC_run_releaser.py``` - Queue processed data for release/import into Bionimbus


# HGAC_run_monitor.py

## Requirements:

```
cffi==1.3.0
cryptography==1.1
Django==1.8.5
docopt==0.4.0
enum34==1.0.4
idna==2.0
ipaddress==1.0.14
mandrill==1.0.57
MySQL-python==1.2.5
ndg-httpsclient==0.4.0
psycopg2==2.6.1
pyasn1==0.1.9
pycparser==2.14
pyOpenSSL==0.15.1
requests==2.8.1
six==1.10.0
SQLAlchemy==1.0.9
zc.lockfile==1.1.0
```

## config.json

```py
{
  "root_dir": "/path/to/Illumina/run/directories",
  "transfer_complete_filename": "RTAComplete.txt",
  "processing_complete_filename": "ProcessingComplete.txt",
  "BaseCalls_dir": "Data/Intensities/BaseCalls",
  "configureBclToFastq": {
    "script": "/path/to/configureBclToFastq.pl",
    "general_options": "--no-eamss --fastq-cluster-count 0 --ignore-missing-control --ignore-missing-stats --ignore-missing-bcl --force",
    "input_dir": "--input-dir Data/Intensities/BaseCalls/",
    "output_dir": "--output-dir Data/Intensities/BaseCalls/Unaligned",
    "sample_sheet": "--sample-sheet Data/Intensities/BaseCalls/SampleSheet.csv"
  },
  "email": {
    "EMAIL_USE_TLS": "True",
    "EMAIL_HOST": "smtp.mandrillapp.com",
    "EMAIL_PORT": "587",
    "EMAIL_HOST_USER": "mandrill_account_name",
    "EMAIL_HOST_PASSWORD": "mandrill secret key"
  },
  "addresses": {
    "to": ["someone@somewhere.email"],
    "cc": [],
	"reply-to": "someone@somewhere.email"
  },
  "seqConfig": {
    "URL_get_config": "http://localhost:8000/seq-config/config/get",
    "URL_post_demultiplex_files": "http://localhost:8000/seq-config/run/demultiplex_file/post",
    "URL_get_runs_by_status": "http://localhost:8000/seq-config/run/get_runs_by_status",
    "URL_set_run_status": "http://localhost:8000/seq-config/run/set_run_status",
    "URL_get_library_status": "http://localhost:8000/seq-config/library/get_library_status"
  }
}
```

## Run command to initiate preprocessing on available run data 

```sh
/path/to/env/python HGAC_run_monitor.py -c config.json
```
