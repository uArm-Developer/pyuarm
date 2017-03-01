from __future__ import print_function
from __future__ import division
import platform
import threading
from ..util import *
from .list_uarms import get_uarm_port_cli
from subprocess import Popen, PIPE, STDOUT
import time
from .. import PY3
if PY3:
    import urllib.request
else:
    import urllib2

__version__ = '1.1.0'
__author__ = 'Alex Tan'
'''
This Tool is for uArm firmware flashing. Also support download firmware online
'''

process = None


def exit_fun():
    try:
        input("\nPress Enter to Exit...")
    except Exception:
        pass


def read_std_output(cmd, progress_step=None):
    global process
    try:
        process = Popen(cmd, stdout=PIPE,
                        stderr=STDOUT, shell=False, bufsize=1)
        progress = 0
        total_progress = 150
        title = "Flashing: "
        while True:
            data = process.stdout.read(1)
            if data == '' or process.poll() is not None:
                break
            if data != '':
                if data == b'#':  # Progress
                    progress += 1
                    if progress_step is None:
                        if get_logger_level() != DEBUG:
                            progressbar(title, progress, total_progress)
                    else:
                        progress_step(progress, total_progress)
                if not progress_step:
                    printf(data, STREAM)
        time.sleep(0.1)
        print("")
        # printf("Flashing EOF", INFO)
        process.wait()
        exitcode = process.returncode
        process.stdout.close()
        process.terminate()
        if exitcode == 1:  # Error

            return
        else:  # succeed
            pass
    except OSError as e:
        # if process is not None:
        #     process.terminate()
        printf("Error Occurred, {}".format(e), ERROR)


def download(url, filepath):  ## To - improve, add logger to support show the download prgress
    try:
        if PY3:
            u = urllib.request.urlopen(url)
            fileTotalbytes = u.length
        else:
            u = urllib2.urlopen(url)
            fileTotalbytes = int(u.info().getheaders("Content-Length")[0])
        printf("writing to {}, file size: {} bytes ".format(filepath, str(fileTotalbytes)))

        data_blocks = []
        total = 0

        while True:
            block = u.read(1024)
            data_blocks.append(block)
            total += len(block)
            title = "Downloading: "
            progressbar(title, total, fileTotalbytes)
            if not len(block):
                break
        print("")

        data = b''.join(data_blocks)  # had to add b because I was joining bytes not strings
        u.close()

        with open(filepath, "wb") as f:
            f.write(data)
    except Exception as e:
        printf("Error: " + str(e))


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
        return None, "Not support System"
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
    return cmd, error_description


def flash(port, firmware_path, avrdude_path=None):
    cmd, error_description = gen_flash_cmd(port, firmware_path, avrdude_path)
    printf("Flash Command:\n{}".format(' '.join(cmd)), INFO)
    try:
        flash_thread = threading.Thread(target=read_std_output, args=(cmd,))
        flash_thread.start()
        # subprocess.call(cmd)
    except OSError as e:
        printf(("Error occurred: error code {0}, error msg: {1}".format(str(e.errno), e.strerror)), DEBUG)
        printf(error_description, ERROR)


def main(args):

    if args.debug:
        set_default_logger(debug=True)
        set_stream_logger()
    else:
        set_default_logger()

    if args.port:
        port_name = args.port
    else:
        port_name = get_uarm_port_cli()

    if args.path:
        firmware_path = args.path
    else:
        firmware_path = os.path.join(ua_dir, default_config['firmware_filename'])

    if args.download:
        download(default_config['firmware_url'], firmware_path)

    if port_name is not None:
        flash(port_name, firmware_path)
    else:
        printf("No uArm Port Found", ERROR)


if __name__ == '__main__':
    try:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--port", help="specify port number")
        parser.add_argument("--path", help="firmware path")
        parser.add_argument("--debug", help="open Debug Mode", action="store_true")
        parser.add_argument("-d", "--download",
                            help="download firmware from {}".format(default_config['firmware_url']),
                            action="store_true")
        args = parser.parse_args()
        main(args)
    except SystemExit:
        exit_fun()
