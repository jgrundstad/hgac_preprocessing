import argparse

__author__ = 'A. Jason Grundstad'


def main():
    parser = argparse.ArgumentParser(description='Scan runs for those queued for release.')
    parser.add_argument('-c', '--config', desc='config_file', required=True,
                        help='Config file (.json)')
    args = parser.parse_args()


if __name__ == '__main__':
    main()