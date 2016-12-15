from __future__ import print_function
from __future__ import division

__version__ = '1.1.0'
__author__  = 'Alex Tan'
'''
This Tool is for uArm firmware flashing. Also support download firmware online
'''

import sys
import os
import platform
import subprocess
from ..util import printf,ua_dir
from .list_uarms import get_uarm_port_cli


if sys.version > '3':
    PY3 = True
else:
    PY3 = False

if PY3:
    import urllib.request
else:
    import urllib2

default_config = {
    "filename": "firmware.hex",
    "hardware_id": "USB VID:PID=0403:6001",
    "download_url": "http://download.ufactory.cc/firmware/firmware_dev.hex",
    "download_flag": False
}



def exit_fun():
    try:
        input("\nPress Enter to Exit...")
    except Exception:
        pass

def download(url, filepath): ## To - improve, add logger to support show the download prgress
    try:
        if PY3:
            u = urllib.request.urlopen(url)
            fileTotalbytes = u.length
        else:
            u = urllib2.urlopen(url)
            fileTotalbytes = int(u.info().getheaders("Content-Length")[0])
        print ("writing to {}, file size: {} bytes ".format(filepath, str(fileTotalbytes)))

        data_blocks = []
        total=0

        while True:
            block = u.read(1024)
            data_blocks.append(block)
            total += len(block)
            hash = ((60*total)//fileTotalbytes)
            per =total / fileTotalbytes
            if PY3:
                print("[{}{}] {:.0%}".format('#' * hash, ' ' * (60-hash), per), end="\r")
            else:
                print("[{}{}] {:.0%}".format('#' * hash, ' ' * (60 - hash), per), end="\r")
            if not len(block):
                print ("\nCompleted!")
                break

        data=b''.join(data_blocks) #had to add b because I was joining bytes not strings
        u.close()


        with open(filepath, "wb") as f:
                f.write(data)
    except Exception as e:
        print ("Error: " + str(e))


def gen_flash_cmd(port, firmware_path, avrdude_path=None, debug=False):
    if platform.system() == 'Darwin':
        avrdude_bin = 'avrdude'
        error_description = "avrdude is required, Please use `brew install avrdude`"

    elif platform.system() == 'Windows':
        avrdude_bin = 'avrdude.exe'
        error_description = "avrdude is required, Please install winavr..."

    elif platform.system() == 'Linux':
        avrdude_bin = 'avrdude'
        error_description = "avrdude is required, Please use `sudo apt-get install avrdude`"
    else:
        return None,"Not support System"
    cmd = []
    if avrdude_path is not None:
        cmd.append(os.path.join(avrdude_path, avrdude_bin))
        cmd.append(os.path.join(avrdude_path, 'avrdude.conf'))
    else:
        cmd.append(avrdude_bin)
    cmd.append('-patmega328p')
    cmd.append('-carduino')
    cmd.append('-P{}'.format(port))
    cmd.append('-b115200')
    cmd.append('-D')
    cmd.append('-Uflash:w:{}:i'.format(firmware_path))
    if debug:
        cmd.append('-v')
    return cmd,error_description


def flash(port, firmware_path, avrdude_path=None):
        cmd,error_description = gen_flash_cmd(port,firmware_path,avrdude_path)
        printf("Flash Command: {}".format(' '.join(cmd)))
        try:
            subprocess.call(cmd)
        except OSError as e:
            print(("Error occurred: error code {0}, error msg: {1}".format(str(e.errno), e.strerror)))
            print(error_description)

def main(args):
    if args.port:
        port_name = args.port
    else:
        port_name = get_uarm_port_cli()
    if args.path:
        firmware_path = args.path
    else:
        firmware_path = os.path.join(ua_dir, default_config['filename'])

    if args.download:
        download(default_config['download_url'], firmware_path)

    if port_name is not None:
        flash(port_name, firmware_path)
    else:
        printf("No uArm Port Found")

if __name__ == '__main__':
    try:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--port", help="specify port number")
        parser.add_argument("--path", help="firmware path")
        parser.add_argument("-d", "--download",
                        help="download firmware from {}".format(default_config['download_url']),
                        action="store_true")
        args = parser.parse_args()
        main(args)
    except SystemExit:
        exit_fun()


