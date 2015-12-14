# hgac_preprocessing
Illumina preprocessing daemon

The hgac_preprocessing software relies on an HGAC SeqConfig web application service for
managing and performing Illumina bcl conversion and demultiplexing processes.
 
This repository contains 2 primary components:

1. [HGAC_run_monitor.py](#hgac_run_monitorpy) - Watch the defined root data directory for completed sequencing runs,
and perform preprocessing as described by each run's parameters.
2. [HGAC_run_releaser.py](#hgac_run_releaserpy) - Queue processed data for release/import into Bionimbus

Emailing service is handled via Mandrill: [https://mandrillapp.com]

---

## HGAC_run_monitor.py

1. Search local directories for newly completed sequencing run
2. Search SeqConfig for matching run configuration
3. Demultiplex:
  a. Must be performed once per barcode length (if there are multiple barcode lengths in the run) 
  b. Demultiplexing is performed by Illumina's [Bcl2Fastq Conversion Software](https://support.illumina.com/downloads/bcl2fastq_conversion_software_184.html)
  c. Fastq data is renamed to our conventions, and linked to a <run_name>/TEMP/ directory

### Requirements:

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

### config.json

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

### Run command to initiate preprocessing on available run data 

```sh
/path/to/env/python HGAC_run_monitor.py -c config.json
```
\* may be run as a cron-job 



## HGAC_run_releaser.py

1. Check filesystem for newly processed run directory
2. Check SeqConfig for newly released run names
3. Break symlinks in ```<run_dir>/TEMP``` for data marked to be held back.
3. Queue the run for the release/import process:
  a. ```mv <run_dir>/TEMP COMPLETED```
  b. ```touch <run_dir>/COMPLETED/sync.me```

### Requirements
Same as above

### config.json
Same as above

### Run command to initiate data release

```sh
/path/to/env/python HGAC_run_releaser.py -c config.json
```
