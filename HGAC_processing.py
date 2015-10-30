import os
import sys

__author__ = 'A. Jason Grundstad'


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


def generate_sample_sheet(run_config=None, lanes=None, path=None):
    """
    example:

    D0MDRACXX,7,2012-18,,ACCAAC,TS9,N,R1,tech_name,submitter
    D0MDRACXX,7,2012-19,,AACTCC,TS11,N,R1,tech_name,submitter
    D0MDRACXX,7,2012-20,,TAATGC,TS16,N,R1,tech_name,submitter
    D0MDRACXX,7,2012-7,,GCTCGA,TS8,N,R1,tech_name,submitter
    D0MDRACXX,8,2012-18,,,,N,R1,tech_name,submitter

    :param run_config: dict
    :param lanes: list
    :param path: /location/of/outfile
    :return:
    """
    sample_sheet_path = os.path.join(path, 'SampleSheet.csv')
    flowcell_id = run_config['run_name'].split('_')[3][1:]
    try:
        sample_sheet = open(sample_sheet_path, 'w')
    except:
        print >>sys.stderr, "ERROR: Unable to open {} for writing.".format(
            sample_sheet_path
        )
        raise
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


def process_run(run_config=None, config=None):

    cmd = build_configureBclToFastq_command(run_config=run_config, config=config)
    print cmd

    lane_collections = collect_lanes_by_barcode_len(run_config=run_config)

    base_calls_dir = os.path.join(config['root_dir'], run_config['run_name'],
                                  config['BaseCalls_dir'])

    for barcode_length in lane_collections:
        """
        The conversion software must run once for each barcode length,
        requiring newly generated SampleSheet.csv files each time
        """
        # build samplesheet
        generate_sample_sheet(run_config=run_config,
                              lanes=lane_collections[barcode_length],
                              path=base_calls_dir)
        # execute configureBclToFastq
        # execute make -j <num cores>
        # mv Unaligned to Unaligned<barcode_len>
        pass
