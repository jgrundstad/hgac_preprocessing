import argparse

from HGAC_run_monitor import parse_config

__author__ = 'A. Jason Grundstad'


class Releaser():

    def __init__(self, config_file=None):
        self.config = parse_config(config_file=config_file)


    def find_completed(self):
        pass


def main():
    parser = argparse.ArgumentParser(description='Scan runs for those queued for release.')
    parser.add_argument('-c', '--config', desc='config_file', required=True,
                        help='Config file (.json)')
    args = parser.parse_args()

    r = Releaser(config_file=args.config)





if __name__ == '__main__':
    main()