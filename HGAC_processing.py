import glob
import os
import subprocess
import sys
import multiprocessing

import re

__author__ = 'A. Jason Grundstad'


def collect_lanes_by_barcode_len(run_config=None):
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


def build_configureBclToFastq_command(run_config=None, config=None):
    """
    generate one command per barcode length.  usually 6 or 8
    :param run_config:
    :param config:
    :return: list
    """
    bcl_dict = config['configureBclToFastq']
    binary = bcl_dict['script']
    general_options = bcl_dict['general_options']
    input_dir = bcl_dict['input_dir']
    output_dir = bcl_dict['output_dir']
    sample_sheet = bcl_dict['sample_sheet']

    base_mask = '--use-bases-mask Y{}'.format(run_config['read1_cycles'])
    if run_config['barcode_cycles'] is not 'null':
        base_mask += ',I{}'.format(run_config['barcode_cycles'])
    if run_config['read2_cycles'] is not 'null':
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
            submitter = run_config['Lanes'][lane][bnid]['submitter']
            barcode_name = run_config['Lanes'][lane][bnid]['barcode_name']
            barcode_seq = run_config['Lanes'][lane][bnid]['barcode_seq']
            if barcode_name == 'null':
                barcode_name = ''
                barcode_seq = ''
            print >>sample_sheet, ','.join([flowcell_id, lane, bnid, '', barcode_seq,
                                            barcode_name, 'N', 'R1', 'tech', submitter])

    # build config.txt
    analysis_type = 'sequence'
    if 'paired' in run_config['run_type']:
        analysis_type += '_pair'
    print "run_type {} analysis_type {}  lanes {}".format(run_config['run_type'], analysis_type, lanes)
    print >>config_file, '{}:ANALYSIS {}'.format(
        ''.join(str(x) for x in sorted(lanes)), analysis_type
    )


def bcl_to_fastq(run_config=None, config=None):
    """
    This needs to be performed in the /raid/illumina_production/<run_name> dir
    runs the BCLToFastq Illumina software, configuring the demultiplexing,
    which is executed then with a 'make' command over the available cores
    :param run_config:
    :param config:
    :return:
    """
    cpu_count = multiprocessing.cpu_count()
    os.chdir(os.path.join(config['root_dir'], run_config['run_name']))
    cmd = build_configureBclToFastq_command(run_config=run_config, config=config)
    args = cmd.split(' ')
    try:
        with open('configureBclToFastq.log.out', 'w') as out, \
                open('configureBclToFastq.log.err', 'w') as err:
            subprocess.Popen(args, stdout=out, stderr=err)
    except:
        print >>sys.stderr, "ERROR: unable to run configureBclToFastq.  Exiting."
        raise

    os.chdir('Data/Intensities/BaseCalls/Unaligned')
    try:
        with open('BclToFastq.log.out', 'w') as out, open('BclToFastq.log.err', 'w') as err:
            subprocess.Popen(['make', '-j', cpu_count], stdout=out, stderr=err)
    except:
        print >>sys.stderr, "ERROR: unable to run 'make' ({})".format(os.getcwd())
        raise
    os.chdir(os.path.join(config['root_dir'], run_config['run_name']))


def link_files(run_config=None, config=None):
    os.chdir('TEMP')
    # find all unaligned, non-undetermined files
    files = glob.glob('../Data/Intensities/BaseCalls/Unaligned/Project_*/*/*.fastq.gz')
    for f in files:
        old_filename = f.split('/')[-1]
        print "old filename {}".format(old_filename)
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

        os.symlink(f, new_filename)


def process_run(run_config=None, config=None):

    lane_collections = collect_lanes_by_barcode_len(run_config=run_config)

    base_calls_dir = os.path.join(config['root_dir'], run_config['run_name'],
                                  config['BaseCalls_dir'])

    #  TEMP directory will hold all symlinks to processed data
    os.mkdir(os.path.join(config['root_dir'], run_config['run_name'], 'TEMP'))

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
        bcl_to_fastq(run_config=run_config, config=config)

    # link files, md5sums, fastqc processing
    link_files(run_config=run_config, config=config)

