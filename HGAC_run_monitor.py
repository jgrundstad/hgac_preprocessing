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

__author__ = 'A. Jason Grundstad'


def find_unprocessed(root_dir=None, config=None):
    """
    return run names (only) of unprocessed runs (don't contain
    the ProcessingComplete.txt file)
    :param root_dir:
    :param config:
    :return:
    """
    print "preprocessing_complete_filename: {}".format(config['processing_complete_filename'])
    print "Searching: {}".format(os.path.join(root_dir, '*', config['processing_complete_filename']))
    transferred_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['transfer_complete_filename']))]
    processed_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['processing_complete_filename']))]
    return list(set(transferred_runs) - set(processed_runs))


def parse_config(config_file=None):
    with open(config_file) as f:
        data = f.read()
    return json.loads(data)


def start_processing(run_name=None, config=None):
    config_request = requests.get('/'.join([config['seqConfig']['URL_get_config'], run_name]))
    run_config = json.loads(config_request.text)
    Hp.process_run(run_config=run_config, config=config)


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
    # parser.add_argument('-f', '--force', action='store_true',
    #                     help='remove existing files')
    args = parser.parse_args()

    config = parse_config(config_file=args.config_file)

    lock = set_lockfile()
    unprocessed_runs = find_unprocessed(root_dir=config['root_dir'], config=config)
    print unprocessed_runs

    if len(unprocessed_runs) > 0:
        # set the "processed" file to avoid re-firing off the job if something goes wrong
        # manually remove it to queue up for processing
        os.mknod(os.path.join(config['root_dir'], unprocessed_runs[0],
                              config['processing_complete_filename']))
        start_processing(run_name=unprocessed_runs[0], config=config)

    lock.close()


if __name__ == '__main__':
    main()
