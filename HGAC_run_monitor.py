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
    #print "preprocessing_complete_filename: {}".format(config['processing_complete_filename'])
    #print "Searching: {}".format(os.path.join(root_dir, '*', config['processing_complete_filename']))
    transferred_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['transfer_complete_filename']))]
    processed_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['processing_complete_filename']))]
    return list(set(transferred_runs) - set(processed_runs))


def parse_config(config_file=None):
    with open(config_file) as f:
        data = f.read()
    return json.loads(data)


def get_run_config(config=None, run_name=None):
    config_request = requests.get('/'.join([config['seqConfig']['URL_get_config'], run_name]))
    return json.loads(config_request.text)


def set_lockfile(lockfile=None):
    try:
        l_file = zc.lockfile.LockFile(lockfile)
        return l_file
    except zc.lockfile.LockError:
        print "ERROR: HGAC_run_monitor.py appears to be running. Very lockfile, much stopping!"
        print "{}".format(lockfile)
        sys.exit(1)


def manual_lockfile(lockfile_name=None):
    if os.path.exists(lockfile_name):
        sys.exit(0)
    else:
        os.mknod(lockfile_name)


def main():
    parser = argparse.ArgumentParser(description='Scan for new Illumina runs. ' +
                                     'Fire off preprocessing/demultiplexing.')
    parser.add_argument('-c', '--config', dest='config_file',
                        help='Config file (.json)', required=True)
    # parser.add_argument('-f', '--force', action='store_true',
    #                     help='remove existing files')
    args = parser.parse_args()

    config = parse_config(config_file=args.config_file)

    #lockfile = set_lockfile(lockfile=os.path.join(config['root_dir'], 'preprocessing.lock'))
    lockfile = os.path.join(config['root_dir'], 'preprocessing.lock')
    manual_lockfile(lockfile)

    unprocessed_runs = find_unprocessed(root_dir=config['root_dir'], config=config)
    # print "Unprocessed runs:"
    # print unprocessed_runs

    try:
        if len(unprocessed_runs) > 0:
            # Is the run approved?
            response = requests.get(os.path.join(config['seqConfig']['URL_get_runs_by_status'], '1/'))
            print response.text
            for run_name in unprocessed_runs:
                if run_name in json.loads(response.text).values():
                    # set the "processed" file to avoid re-firing off the job if something goes wrong
                    # manually remove it to queue up for processing
                    os.mknod(os.path.join(config['root_dir'], unprocessed_runs[0],
                                          config['processing_complete_filename']))
                    run_config = get_run_config(config, run_name=run_name)
                    Hp.process_run(run_config=run_config, config=config)
                    break # just do the first approved and stop
                else:
                    print "Run {} does not have an approved config file available".format(
                        run_name
                    )
    except Exception, e:
        print "raised this exception: {}".format(e)
        raise

    #print "Closing Lockfile."
    #lockfile.close()
    os.remove(lockfile)


if __name__ == '__main__':
    main()
