import argparse
import glob
import json
import os

import requests

from HGAC_run_monitor import parse_config

__author__ = 'A. Jason Grundstad'


class Releaser():

    def __init__(self, config_file=None):
        self.config = parse_config(config_file=config_file)

    def go(self):
        completed_run_names = set(self.find_completed())
        print "Completed: "
        print completed_run_names
        released_run_names = set(self.find_released())
        print "Released: "
        print released_run_names
        to_be_released = completed_run_names.intersection(released_run_names)
        print "To Be Released: "
        print to_be_released
        for run_name in to_be_released:
            self.release_run(run_name)
            self.update_run_status(run_name, '6')

    def find_completed(self):
        os.chdir(self.config['root_dir'])
        processing_complete = glob.glob('*/ProcessingComplete.txt')
        return [path.split(os.path.sep)[0] for path in processing_complete]

    def find_released(self):
        r = requests.get(os.path.join(self.config['seqConfig']['URL_get_runs_by_status'], '5/'))
        return json.loads(r.text).values()

    def release_run(self, run_name):
        os.chdir(os.path.join(self.config['root_dir'], run_name, 'TEMP'))
        fastq_files = glob.glob('*_sequence.txt.gz')
        for fastq_file in fastq_files:
            status = self.get_release_status_for_file(filename=fastq_file)
            if status == 1:
                os.remove(fastq_file)
        os.chdir('..')
        os.rename('TEMP', 'COMPLETED')
        os.mknod(os.path.join('COMPLETED', 'sync.me'))

    def get_release_status_for_file(self, filename=None):
        toks = filename.split('_')
        bionimbus_id = toks[0]
        run_name = '_'.join(toks[1:4])
        lane_number = toks[5]
        response = requests.get(os.path.join(self.config['seqConfig']['URL_get_library_status'],
                                             run_name, lane_number, bionimbus_id))
        return json.loads(response.text)[bionimbus_id]

    def update_run_status(self, run_name, status):
        response = requests.get(os.path.join(self.config['seqConfig']['URL_set_run_status'],
                                             status))
        print response.text


def main():
    parser = argparse.ArgumentParser(description='Scan runs for those queued for release.')
    parser.add_argument('-c', '--config', dest='config_file', required=True,
                        help='Config file (.json)')
    args = parser.parse_args()

    r = Releaser(config_file=args.config_file)
    r.go()


if __name__ == '__main__':
    main()