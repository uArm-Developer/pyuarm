from __future__ import print_function
from __future__ import division
import platform
import threading
import os
from ..util import progressbar
from ..log import get_logger_level, printf, ERROR, DEBUG, STREAM, set_default_logger, set_stream_logger, INFO
from ..config import get_online_config, save_default_config, save_config, load_config, ua_dir, home_dir
from .list_uarms import get_uarm_port_cli
from subprocess import Popen, PIPE, STDOUT
import subprocess
from ..version import check_version_update
import time
from .. import PY3
if PY3:
    import urllib.request
else:
    import urllib2


__version__ = '1.1.1'
__author__ = 'Alex Tan'
'''
This Tool is for uArm firmware flashing. Also support download firmware online
'''

process = None
error_description = None


def exit_fun():
    try:
        input("\nPress Enter to Exit...")
    except Exception:
        pass


def catch_exception(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError as e:
            if e.errno == 2:
                printf("{}".format(error_description), ERROR)
        except Exception as e:
            printf("{} - {} - {}".format(type(e).__name__, func.__name__, e), ERROR)
    return decorator


@catch_exception
def read_std_output(cmd, progress_step=None):
    global process
    process = Popen(cmd, stdout=PIPE,
                    stderr=STDOUT, shell=False, bufsize=1)
    progress = 0
    total_progress = 100
    while True:
        data = process.stdout.read(1)
        if data == '' or process.poll() is not None:
            break
        if data != '':
            if data == b'#':  # Progress
                progress += 1
                if progress >= 50 and progress_step:  # ignore first 50 '#'
                    progress_step(progress-50, total_progress)
    time.sleep(0.1)
    print("")
    process.wait()
    exitcode = process.returncode
    process.stdout.close()
    process.terminate()
    if exitcode == 1:  # Error
        return
    else:  # succeed
        pass


@catch_exception
def download(url, filepath):  # To - improve, add logger to support show the download prgress
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


def gen_flash_cmd(port, firmware_path, avrdude_path=None, debug=False):
    global error_description
    if platform.system() == 'Darwin':
        avrdude_bin = 'avrdude'
        error_description = "avrdude is required, Please use `brew install avrdude` "
    elif platform.system() == 'Windows':
        avrdude_bin = 'avrdude.exe'
        error_description = "avrdude is required, Please install winavr from " \
                            "https://sourceforge.net/projects/winavr/files/WinAVR/20100110/"
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
    return cmd


@catch_exception
def flash(port, firmware_path, avrdude_path=None):
    cmd = gen_flash_cmd(port, firmware_path, avrdude_path)
    printf("Flash Command:\n{}".format(' '.join(cmd)), INFO)
    title = "Flashing: "

    def progress_step(progress, total):
        progressbar(title, progress, total)
    if get_logger_level() != DEBUG:
        flash_thread = threading.Thread(target=read_std_output, args=(cmd, progress_step, ))
        flash_thread.start()
    else:
        cmd.append('-v')
        subprocess.call(cmd)


def get_latest_firmware_version(branch='pro'):
    try:
        config = get_online_config()
        if branch == 'pro':
            vs = config['data']['firmware']['pro']
        elif branch == 'dev':
            vs = config['data']['firmware']['dev']
        versions = {}
        for v in vs:
            versions = {v['version']: v['url']}
        latest_version = max(versions.keys())
        latest_version_url = versions[latest_version]
        settings = load_config()
        if settings['latest_version'] != "":
            if check_version_update(latest_version, settings['latest_version']):
                settings['latest_version'] = latest_version
                settings['firmware_url'] = latest_version_url
                save_config(settings)
    except KeyError:
        save_default_config()


def main(args):
    settings = load_config()
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
        firmware_path = os.path.join(ua_dir, settings['firmware_filename'])

    if args.download:
        download(settings['firmware_url'], firmware_path)

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
        parser.add_argument("-d", "--download", help="download firmware online", action="store_true")
        args = parser.parse_args()
        main(args)
    except SystemExit:
        exit_fun()
