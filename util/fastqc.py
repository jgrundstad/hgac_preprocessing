import glob
import os
import multiprocessing

import job_manager

__author__ = 'A. Jason Grundstad'


def run_fastqc(config=None, run_config=None):
    os.chdir(os.path.join(config['root_dir'], run_config['run_name']))
    try:
        os.mkdir(config['qc']['dir'])
    except OSError:
        print 'Warning: {} directory already exists, which is ok.'.format(
                config['qc']['dir'])
    os.chdir(os.path.join(config['root_dir'], run_config['run_name'], 'TEMP'))
    jobs = []
    for fastq in glob.glob('*_sequence.txt.gz'):
        cmd = '{fastqc} -j {java} -o {QC} {fastq}'.format(
            fastqc=config['qc']['fastqc'], java=config['qc']['java'],
            QC=os.path.join(config['root_dir'], run_config['run_name'], config['qc']['dir']),
            fastq=fastq)
        print 'appending cmd: {}'.format(cmd)
        jobs.append(cmd)
    job_manager.job_manager(cmd_list=jobs, threads=multiprocessing.cpu_count(), interval=20)


def send_fastqc_to_server(config=None, run_config=None):
    os.chdir(os.path.join(config['root_dir'], run_config['run_name'], config['qc']['dir']))
    cmd = 'rsync -av --progress --stats *html {}/{}/'.format(config['qc']['server'],
                                                             run_config['run_name'])
    job_manager.job_manager([cmd], threads=1, interval=10)
