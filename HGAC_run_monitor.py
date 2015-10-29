"""
Process to identify completely transferred Illumina runs, retrieve
the configuration settings from the seqConfig service

run as cronjob
"""
import argparse
import glob
import json
import os
import sys

import zc.lockfile
import requests

import HGAC_processing as Hp

__author__ = 'jgrundst'


def find_unprocessed(root_dir=None, config=None):
    transferred_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['transfer_complete_filename']))]
    processed_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['processing_complete_filename']))]
    return list(set(transferred_runs) - set(processed_runs))


def parse_config(config_file=None):
    with open(config_file) as f:
        data = f.read()
    return json.loads(data)


def process_run(run_name=None, config=None):
    config_request = requests.get('/'.join([config['seqConfig']['URL_get_config'], run_name]))
    run_config = json.loads(config_request.text)
    preprocessing_cmds = Hp.build_preprocessing_cmds(run_config=run_config, config=config)


def set_lockfile():
    try:
        return zc.lockfile.LockFile('preprocessing')
    except zc.lockfile.LockError:
        print "ERROR: HGAC_run_monitor.py appears to be running. Very lockfile, much locked!"
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Scan for new Illumina runs. ' +
                                     'Fire off preprocessing/demultiplexing.')
    parser.add_argument('-c', '--config', dest='config_file',
                        help='Config file (.json)', required=True)
    args = parser.parse_args()

    config = parse_config(config_file=args.config_file)

    lock = set_lockfile()
    unprocessed_runs = find_unprocessed(root_dir=config['root_dir'])
    print unprocessed_runs

    if len(unprocessed_runs) > 0:
        process_run(run_name=unprocessed_runs[0], config=config)

    lock.close()


if __name__ == '__main__':
    main()
