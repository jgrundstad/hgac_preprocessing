import argparse
import os
__author__ = 'jgrundst'


def find_unprocessed(root_dir=None):
    pass


def main():
    parser = argparse.ArgumentParser(description="Scan for new Illumina runs." +
                                     " Fire off preprocessing/demultiplexing.")
    parser.add_argument('-c', '--config', dest='config_file',
                        help='Config file (.json)', required=True)
    args = parser.parse_args()
    print "Config file {}".format(args.config_file)


if __name__ == '__main__':
    main()
