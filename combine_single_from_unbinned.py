import argparse
import glob
import os
from subprocess import check_call


def get_fastqs(path=None):
    fastqs = list()
    for fq in glob.glob(path):
        fastqs.append(fq)
    return fastqs


def convert_unbinned(unbinned_list=None, demuxed_list=None, lane=None):
    # conv = '/home/jgrundst/src/Illumina_preprocessing/convert_stream_sanger-illumina.pl'
    for f in unbinned_list:
        # which end are we?
        end = '1'
        if '_R2_' in f:
            end = '2'
        # get corresponding read end from demuxed
        demuxed_file = ''
        for d in demuxed_list:
            if 'X_' + lane + '_sequence.txt.gz' in d:
                demuxed_file = d
            elif 'X_' + lane + '_' + end + '_sequence.txt.gz' in d:
                demuxed_file = d

        # convert and append
        print "streaming conversion of " + f + " into " + demuxed_file
        cmd_string = 'cat ' + f + ' >> ' + demuxed_file
        print "CMD_STRING= %s" % cmd_string
        check_call(cmd_string, shell=True)
        print ''


def main():
    parser = argparse.ArgumentParser("Merge the unbinned reads into a single-" +
                                     "lane sample.")
    parser.add_argument('-r', '--run_dir', action='store', dest='run_dir',
                        help='Run directory', required=True)
    parser.add_argument('-l', '--lane', action='store', dest='lane',
                        help='Lane number', required=True)
    args = parser.parse_args()

    demuxed_glob = args.run_dir + "/Data/Intensities/BaseCalls/Unaligned*/Project*/*/*X_" + args.lane + "_*.txt.gz"
    demuxed_fastqs = get_fastqs(path=demuxed_glob)

    unbinned_glob = os.path.join(args.run_dir,
                                 "/Data/Intensities/BaseCalls/Unaligned*/Undetermined_indices/Sample_lane",
                                 args.lane,
                                 "/*fastq.gz")
    unbinned_fastqs = get_fastqs(path=unbinned_glob)

    convert_unbinned(unbinned_list=unbinned_fastqs, lane=args.lane,
                     demuxed_list=demuxed_fastqs)


if __name__ == '__main__':
    main()
