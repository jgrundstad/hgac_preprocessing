import glob
import os
import socket
import sys
import subprocess
import multiprocessing
import re
import json

import requests

from util import emailer
from util import fastqc

__author__ = 'A. Jason Grundstad'


def get_hostname():
    return socket.gethostname()


def collect_lanes_by_barcode_len(run_config=None):
    """
    demultiplexing can only be done over barcodes of similar length.
    :param run_config:
    :return:
    """
    lanes_by_barcode_length = dict()
    for lane in run_config['Lanes']:
        for bnid in run_config['Lanes'][lane]:
            barcode_seq = run_config['Lanes'][lane][bnid]['barcode_seq']
            if barcode_seq != 'null':
                lanes_by_barcode_length[lane] = len(barcode_seq)
    return_d = {}
    for k, v in lanes_by_barcode_length.iteritems():
        return_d.setdefault(v, []).append(k)
    return return_d


def build_configureBclToFastq_command(run_config=None, config=None,
                                      barcode_len=None):
    """
    generate one command per barcode length.  usually 6 or 8
    :param run_config:
    :param config:
    :param barcode_len:
    :return: list
    """
    bcl_dict = config['configureBclToFastq']
    binary = bcl_dict['script']
    general_options = bcl_dict['general_options']
    input_dir = bcl_dict['input_dir']
    output_dir = bcl_dict['output_dir']
    sample_sheet = bcl_dict['sample_sheet']

    base_mask = '--use-bases-mask Y{}'.format(run_config['read1_cycles'])
    if run_config['barcode_cycles'] > 0:
        base_mask += ',I{}'.format(barcode_len)
        """
        on occasion the barcode cycles run on the machine are greater than those needed
        for demultiplexing.  Add N's to the end of the Index mask to account for those.
        """
        for i in range(barcode_len, run_config['barcode_cycles']):
            base_mask += 'N'
    if run_config['read2_cycles'] is not None:
        base_mask += ',Y{}'.format(run_config['read2_cycles'])

    return ' '.join([binary, general_options, input_dir, output_dir, sample_sheet, base_mask])


def generate_support_files(run_config=None, config=None, lanes=None, path=None):
    """
    generate the SampleSheet.csv and config.txt files
    example:

    /raid/illumina_production/<run>/Data/Intensities/BaseCalls/SampleSheet.csv

    FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
    D0MDRACXX,7,2012-18,,ACCAAC,TS9,N,R1,tech_name,submitter
    D0MDRACXX,7,2012-19,,AACTCC,TS11,N,R1,tech_name,submitter
    D0MDRACXX,7,2012-20,,TAATGC,TS16,N,R1,tech_name,submitter
    D0MDRACXX,7,2012-7,,GCTCGA,TS8,N,R1,tech_name,submitter
    D0MDRACXX,8,2012-18,,,,N,R1,tech_name,submitter

    /raid/illumina_production/<run>/config.txt

    :param run_config: dict
    :param config: dict
    :param lanes: list
    :param path: /location/of/outfile
    :return:
    """
    sample_sheet_path = os.path.join(path, 'SampleSheet.csv')
    config_file_path = os.path.join(config['root_dir'], run_config['run_name'], 'config.txt')
    flowcell_id = run_config['run_name'].split('_')[3][1:]
    try:
        sample_sheet = open(sample_sheet_path, 'w')
        config_file = open(config_file_path, 'w')
    except:
        print >>sys.stderr, "ERROR: Unable to open {}, or {} for writing.".format(
            sample_sheet_path, config_file_path
        )
        raise

    # SampleSheet.csv header
    print >>sample_sheet, "FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject"
    for lane in lanes:
        for bnid in run_config['Lanes'][lane]:
            # submitter must not contain any spaces
            submitter = run_config['Lanes'][lane][bnid]['submitter'].replace(' ', '')
            barcode_name = run_config['Lanes'][lane][bnid]['barcode_name']
            barcode_seq = run_config['Lanes'][lane][bnid]['barcode_seq']
            if barcode_name == 'null':
                barcode_name = ''
                barcode_seq = ''
            print >>sample_sheet, ','.join([flowcell_id, lane, bnid, '', barcode_seq,
                                            barcode_name, 'N', 'R1', 'tech', submitter])

    # build config.txt - describes which lanes will be processed
    analysis_type = 'sequence'
    if 'paired' in run_config['run_type']:
        analysis_type += '_pair'
    print "run_type {} analysis_type {}  lanes {}".format(run_config['run_type'], analysis_type, lanes)
    print >>config_file, '{}:ANALYSIS {}'.format(
        ''.join(str(x) for x in sorted(lanes)), analysis_type
    )


def bcl_to_fastq(run_config=None, config=None, barcode_len=None):
    """
    This needs to be performed in the /raid/illumina_production/<run_name> dir
    runs the BCLToFastq Illumina software in 2 stages:
        1. configuration - build directory structure, and supporting files
        2. run process described in Makefile with 'make' over the available cores
    Also sends announcement emails if processes have errored out
    :param run_config:
    :param config:
    :param barcode_len:
    :return:
    """
    cpu_count = str(multiprocessing.cpu_count())
    os.chdir(os.path.join(config['root_dir'], run_config['run_name']))
    cmd = build_configureBclToFastq_command(run_config=run_config, config=config,
                                            barcode_len=barcode_len)
    try:
        with open(os.path.join(config['root_dir'], run_config['run_name'],
                               'configureBclToFastq.log.out'), 'w') as out, \
                open(os.path.join(config['root_dir'], run_config['run_name'],
                                  'configureBclToFastq.log.err'), 'w') as err:
            print >>out, "{}".format(cmd)
            proc = subprocess.Popen(cmd, stdout=out, stderr=err, shell=True)
            proc.communicate()
            exit_code = proc.returncode
            if exit_code > 0:
                print >>sys.stderr, "ERROR [{}]: configureBclToFastq.pl command failed!!!\nExiting.".format(
                    exit_code
                )
                server_name = get_hostname()
                subj = "Error processing {} : {}".format(server_name, run_config['run_name'])
                content = "Server: {}\nRun name: {}\n Error running 'configureBclToFastq.pl'".format(
                    server_name, run_config['run_name']
                )
                emailer.send_mail(api_key=config['email']['EMAIL_HOST_PASSWORD'],
                                  to=config['addresses']['to'],
                                  cc=config['addresses']['cc'],
                                  reply_to=config['addresses']['reply-to'],
                                  subject=subj, content=content)
                sys.exit(1)
    except:
        print >>sys.stderr, "ERROR: unable to run configureBclToFastq.  Exiting."
        raise

    os.chdir('Data/Intensities/BaseCalls/Unaligned')
    try:
        with open('BclToFastq.log.out', 'w') as out, open('BclToFastq.log.err', 'w') as err:
            proc = subprocess.Popen(['make -j ' + cpu_count], stdout=out, stderr=err, shell=True)
            proc.communicate()
            exit_code = proc.wait()
            if exit_code > 0:
                print >>sys.stderr, "ERROR: make command failed!!!\nExiting."
                server_name = get_hostname()
                subj = "Error processing {} : {}".format(server_name, run_config['run_name'])
                content = "Server: {}\nRun name: {}\n Error running 'make'".format(
                    server_name, run_config['run_name']
                )
                emailer.send_mail(api_key=config['email']['EMAIL_HOST_PASSWORD'],
                                  to=config['addresses']['to'],
                                  cc=config['addresses']['cc'],
                                  reply_to=config['addresses']['reply-to'],
                                  subject=subj, content=content)
                sys.exit(1)
    except:
        print >>sys.stderr, "ERROR: unable to run 'make' ({})".format(run_config['run_name'])
        raise
    os.chdir('..')
    try:
        os.rename('Unaligned', 'Unaligned' + str(barcode_len))  # in case multiple demux cycles are required
    except OSError:
        print >>sys.stderr, "Warning! moving Unaligned{} directory to Unaligned{}.old".format(
            str(barcode_len)
        )
        os.rename('Unaligned' + str(barcode_len), 'Unaligned' + str(barcode_len + '.old'))
        os.rename('Unaligned', 'Unaligned' + str(barcode_len))

    os.rename('SampleSheet.csv', 'SampleSheet' + str(barcode_len) + '.csv')
    os.chdir(os.path.join(config['root_dir'], run_config['run_name']))


def link_files(run_config=None):
    """
    search the run directory structure to find all generated fastq.gz files.
    Link them to the <run_dir>/TEMP directory with proper naming
    :param run_config:
    """
    os.chdir('TEMP')
    # find all unaligned, non-undetermined files
    files = glob.glob('../Data/Intensities/BaseCalls/Unaligned*/Project_*/*/*.fastq.gz')
    for f in files:
        old_filename = f.split('/')[-1]
        m = re.match(r'(?P<bnid>\d+-\d+)_[atgcATGC]+_L00(?P<lane>\d)_R(?P<end>\d)_.*',
                     old_filename)
        if run_config['run_type'] == 'single-end' and m:
            print 'single end'
            new_filename = '{bnid}_{run}_{lane}_sequence.txt.gz'.format(
                bnid=m.group('bnid'), run=run_config['run_name'],
                lane=m.group('lane')
            )
        elif run_config['run_type'] == 'paired-end' and m:
            new_filename = '{bnid}_{run}_{lane}_{end}_sequence.txt.gz'.format(
                bnid=m.group('bnid'), run=run_config['run_name'],
                lane=m.group('lane'), end=m.group('end')
            )
        else:
            print >>sys.stderr, "ERROR: unable to create symlink from {}".format(f)
            raise ValueError
        print "linking {} -> {}".format(f, new_filename)
        try:
            os.symlink(f, new_filename)
        except OSError:
            os.remove(new_filename)
            os.symlink(f, new_filename)
    os.chdir('..')


def find_demultiplex_files():
    """
    cwd will be the run directory
    :return:
    """
    return glob.glob(os.path.join('Data', 'Intensities', 'BaseCalls',
                                  'Unaligned*', '*', 'Demultiplex_Stats.htm'))


def concatenate_demultiplex_html():
    """
    parse the HTML from the DemultiplexStats.htm file(s),
    returning a concatenation of all html in the body tags

    :return: string (html)
    """
    demux_files = find_demultiplex_files()
    final_html = ''
    for demux_file in demux_files:
        with open(demux_file, 'r') as f:
            html = ''
            flag = 0
            for line in f:
                if '</body>' in line:
                    flag = 0
                if flag and '</table>' in line:
                    pass
                elif flag and 'ScrollableTableHeader' in line:
                    html += '<table class="table table-bordered table-condensed">\n'
                elif flag and 'ScrollableTableBody' in line:
                    pass
                elif flag and line == '<p></p>\n' or '<p>bcl2fastq' in line:
                    html += '</table>\n' + line
                elif flag and '<col' not in line:
                    if '</td>' in line or line == '<tr>\n':  # remove return character for easier parsing
                        line = line.rstrip()  # put each library's record in one line of html
                    html += line
                if '<body>' in line:
                    flag = 1
            final_html += '<div><h2Hostname: ' + socket.gethostname() + '</h2>\n' + html + '</div>'
    return final_html


def post_demultiplex_files(config=None, run_name=None):
    """
    Send the parsed html table(s) to seqConfig
    :param run_name:
    :param config:
    """
    os.chdir(os.path.join(config['root_dir'], run_name))
    demux_html = concatenate_demultiplex_html()
    html_json = {"html": demux_html}
    headers = {"Content-type": "application/json"}
    response = requests.post(os.path.join(config['seqConfig']['URL_post_demultiplex_files'],
                                          run_name + '/'),
                             data=json.dumps(html_json),
                             headers=headers)
    print "Post_demultiplex_files response: {}".format(response.text)


def process_run(run_config=None, config=None):
    # send email announcing preprocessing initiation
    subject = "{} - Run {} Preprocessing Initiated".format(socket.gethostname(),
                                                           run_config['run_name'])
    message = "Preprocessing has been started for run\n{}".format(run_config['run_name'])
    emailer.send_mail(api_key=config['email']['EMAIL_HOST_PASSWORD'],
                      to=config['addresses']['to'],
                      cc=config['addresses']['cc'],
                      reply_to=config['addresses']['reply-to'],
                      subject=subject,
                      content=message)
    response = requests.get(os.path.join(config['seqConfig']['URL_set_run_status'],
                                         run_config['run_name'],
                                         '3'))
    print response.text

    # collect the lanes by barcode.  Each barcode length requires its own process.
    lane_collections = collect_lanes_by_barcode_len(run_config=run_config)
    base_calls_dir = os.path.join(config['root_dir'], run_config['run_name'],
                                  config['BaseCalls_dir'])

    #  TEMP directory will hold all symlinks to processed data
    try:
        os.mkdir(os.path.join(config['root_dir'], run_config['run_name'], 'TEMP'))
    except OSError:
        print "TEMP dir already exists.  continuing"

    for barcode_length in lane_collections:
        """
        The conversion software must run once for each barcode length,
        requiring newly generated SampleSheet.csv files each time
        """
        # build samplesheet
        generate_support_files(run_config=run_config, config=config,
                               lanes=lane_collections[barcode_length],
                               path=base_calls_dir)

        # execute configureBclToFastq and make -j num_cores
        bcl_to_fastq(run_config=run_config, config=config, barcode_len=barcode_length)

    # Post-demultiplexing steps:
    # link sequence.txt.gz files
    # TODO md5sums
    # fastqc processing
    link_files(run_config=run_config)
    fastqc.run_fastqc(config=config, run_config=run_config)
    fastqc.send_fastq_to_server(config=config, run_config=run_config)

    # update the run status on seq-config
    response = requests.get(os.path.join(config['seqConfig']['URL_set_run_status'],
                                         run_config['run_name'],
                                         '4'))
    print response.text

    # grab all the demux summary files, email them and send to seq-config
    demultiplex_files = find_demultiplex_files()
    post_demultiplex_files(config=config, run_name=run_config['run_name'])
    subj = 'Preprocessing complete: {}'.format(run_config['run_name'])
    message = '''
Preprocessing complete for run: {}
Server: {}
'''
    message = message.format(run_config['run_name'], socket.gethostname())
    emailer.send_mail(api_key=config['email']['EMAIL_HOST_PASSWORD'],
                      to=config['addresses']['to'], cc=config['addresses']['cc'],
                      reply_to=config['addresses']['reply-to'], subject=subj,
                      content=message, html_files=demultiplex_files)
