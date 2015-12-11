import argparse
import glob
import json
import os
import socket
import requests

from HGAC_run_monitor import parse_config
from util import emailer

__author__ = 'A. Jason Grundstad'


class Releaser:

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
        released_files = []
        removed_files = []
        for fastq_file in fastq_files:
            status = self.get_release_status_for_file(filename=fastq_file)
            if status == 1 or status == 0:
                os.remove(fastq_file)
                removed_files.append(fastq_file)
            elif status == 2:
                released_files.append(fastq_file)
        os.chdir('..')
        os.rename('TEMP', 'COMPLETED')
        os.mknod(os.path.join('COMPLETED', 'sync.me'))
        hostname = socket.gethostname()
        subject = '({}) Run {} released'.format(hostname, run_name)
        message = '''Run {run_name} on {hostname} has been released.

These files have been marked for import:
{imported}

These files will not be released:
{removed}
'''
        message = message.format(run_name=run_name, hostname=hostname,
                                 imported='\n'.join(released_files),
                                 removed='\n'.join(removed_files))

        emailer.send_mail(api_key=self.config['email']['EMAIL_HOST_PASSWORD'],
                          to=self.config['addresses']['to'],
                          cc=self.config['addresses']['cc'],
                          reply_to=self.config['addresses']['reply-to'],
                          subject=subject,
                          content=message)
        self.update_run_status(run_name, '6')

    def get_release_status_for_file(self, filename=None):
        toks = filename.split('_')
        bionimbus_id = toks[0]
        run_name = '_'.join(toks[1:5])
        lane_number = toks[5]
        print "run_name: {}  lane_number: {}  bionimbus_id: {}".format(run_name,lane_number, bionimbus_id)
        response = requests.get(os.path.join(self.config['seqConfig']['URL_get_library_status'],
                                             run_name, lane_number, bionimbus_id + '/'))
        print "response object is of type:".format(type(response))
        return json.loads(response.text)[bionimbus_id]

    def update_run_status(self, run_name, status):
        response = requests.get(os.path.join(self.config['seqConfig']['URL_set_run_status'],
                                             run_name,
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
