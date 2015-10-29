import argparse
import glob
import json
import os
import zc.lockfile
import sys

__author__ = 'jgrundst'

config = dict()


def find_unprocessed(root_dir=None):
    global config
    transferred_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['transfer_complete_filename']))]
    processed_runs = [x.split('/')[3] for x in glob.glob(
        os.path.join(root_dir, '*', config['processing_complete_filename']))]
    return list(set(transferred_runs) - set(processed_runs))


def parse_config(config_file=None):
    with open(config_file) as f:
        data = f.read()
    return json.loads(data)


def main():
    global config
    parser = argparse.ArgumentParser(description='Scan for new Illumina runs. ' +
                                     'Fire off preprocessing/demultiplexing.')
    parser.add_argument('-c', '--config', dest='config_file',
                        help='Config file (.json)', required=True)
    args = parser.parse_args()

    config = parse_config(config_file=args.config_file)

    try:
        zc.lockfile.LockFile('preprocessing')
    except zc.lockfile.LockError:
        print "ERROR: HGAC_preprocessor.py appears to be running. lockfile locked!"
        sys.exit(1)

    unprocessed_runs = find_unprocessed(root_dir=config['root_dir'])
    print unprocessed_runs


if __name__ == '__main__':
    main()
