# hgac_preprocessing
Illumina preprocessing daemon

The hgac_preprocessing software relies on an HGAC SeqConfig web application service for
managing and performing Illumina bcl conversion and demultiplexing processes.
 
This repository contains 2 primary components:
1. HGAC_run_monitor.py - Watch the defined root data directory for completed sequencing runs,
and perform preprocessing as described by each run's parameters.
2. HGAC_run_releaser.py - Queue processed data for release/import into Bionimbus

## HGAC_run_monitor.py
