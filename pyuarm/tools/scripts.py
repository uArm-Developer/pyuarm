import argparse

from . import miniterm, list_uarms, calibrate, firmware
from ..version import __version__


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='cmd')

    parser.add_argument('-v', '--version', action='version', version='pyuarm version: {}'.format(__version__))
    pm = subparsers.add_parser("miniterm")
    pm.add_argument("-p", "--port", help="specify port number")
    pm.add_argument("-d", "--debug", help="Turn on Debug Mode", action="store_true")

    pc = subparsers.add_parser("calibrate")
    pc.add_argument("-p", "--port", help="specify port number")
    pc.add_argument("-d", "--debug", help="Turn on Debug Mode", action="store_true")
    pc.add_argument("-c", "--check", help="Check the calibrate offset values", action="store_true")

    pl = subparsers.add_parser("list")

    pf = subparsers.add_parser("firmware")
    pf.add_argument("-p", "--port", help="specify port number")
    pf.add_argument("--path", help="firmware path")
    pf.add_argument("--debug", help="Turn on Debug Mode", action="store_true")
    pf.add_argument("-d", "--download", help="download firmware online", action="store_true")

    args = parser.parse_args()

    if args.cmd:
        if args.cmd == 'miniterm':
            miniterm.main(args)
        elif args.cmd == 'calibrate':
            calibrate.main(args)
        elif args.cmd == 'list':
            list_uarms.main()
        elif args.cmd == 'firmware':
            firmware.main(args)

if __name__ == '__main__':
    main()
