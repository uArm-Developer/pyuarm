from __future__ import division
from __future__ import print_function
import math
import sys
from . import PY3
import logging
from .version import __version__
import os
from os.path import expanduser
import io
import json
if PY3:
    import urllib.request as req
else:
    import urllib2 as req
# ################################### Config ################################
home_dir = os.path.join(expanduser("~"), "uarm", "")
ua_dir = os.path.join(home_dir, "assistant")

config_file = os.path.join(ua_dir, "config.json")
default_config = {
    "branch": "pro",
    "firmware_filename": "firmware.hex",
    "bluetooth_filename": "bluetooth.hex",
    "hardware_id": "USB VID:PID=0403:6001",
    "calibration_filename": "calibration.hex",
    "calibration_url": "http://download.ufactory.cc/firmware/pro/calibration.hex",
    "firmware_url": "http://download.ufactory.cc/firmware/dev/firmware.hex",
    "driver_url": "http://download.ufactory.cc/driver/ftdi_win.zip",
    "bluetooth_url": "http://download.ufactory.cc/firmware/pro/bluetooth.hex",
    "latest_version": "",
}


def load_config():
    try:
        if not os.path.exists(config_file):
            save_default_config()
        with io.open(config_file, "r", encoding="utf-8") as data_file:
            settings = json.load(data_file)
        return settings
    except Exception as e:
        printf ("Error occured when reading settings. {}".format(e))
        return default_config


def save_config(settings):
    cf = open(config_file, "w")
    json.dump(settings, open(config_file, 'w'),
              sort_keys=False, indent=4)
    cf.close()


def save_default_config():
    json.dump(default_config, open(config_file, 'w'),
              sort_keys=False, indent=4, separators=(',', ': '))
    settings = default_config
    save_config(settings)

# ############## online config file #################
def get_online_config():
    online_config_url = "http://download.ufactory.cc/version.json"
    response = req.urlopen(online_config_url)
    online_config_data = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))
    return online_config_data

# ################################### Log ################################
from logging import DEBUG, ERROR, INFO
STREAM = 55
pylogger = None
stream_logger = None


def get_logger_level():
    if pylogger is not None:
        return pylogger.level


def set_default_logger(debug=False):
    if debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logger = logging.getLogger('pyuarm')
    logger.setLevel(logging_level)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging_level)
    logger.addHandler(ch)
    init_logger(logger)


def init_logger(logger):
    """
    initialize global logger
    :param logger
    :return:
    """
    global pylogger
    pylogger = logger
    printf('pyuarm version: ' + __version__)


def set_stream_logger():
    global stream_logger
    stream_logger = logging.getLogger('UA_STREAM')
    myFormatter = logging.Formatter('%(message)s')
    stream_logger.setLevel(logging.DEBUG)
    sch = logging.StreamHandler()
    sch.setFormatter(myFormatter)
    if PY3:
        sch.terminator = ""
    sch.setLevel(logging.DEBUG)
    stream_logger.addHandler(sch)


def close_logger():
    handlers = pylogger.handlers
    for p in handlers:
        p.close()
        pylogger.removeHandler(p)


def printf(msg, type=INFO):
    """
    global print log function
    :param msg:
    :param type:
    :return:
    """
    if pylogger is None:
        set_default_logger()
    if type == INFO:
        pylogger.info(msg)
    elif type == DEBUG:
        pylogger.debug(msg)
    elif type == ERROR:
        pylogger.error(msg)
    elif type == STREAM:
        if pylogger.level == DEBUG:
            if PY3:
                if stream_logger is None:
                    set_stream_logger()
                stream_logger.debug(msg.decode(encoding=sys.getdefaultencoding()))
            else:
                print(msg, end='')

# ################################### Exception ################################


class UArmConnectException(Exception):
    def __init__(self, errno, message=None):
        """
        uArm Connect Exception
        :param errno: 0 Unable to connect uArm, 1 unknown firmware version, 2 unsupported uArm Frimware version
        :param message:
        """
        if message is None:
            self.message = ""
        else:
            self.message = message
        self.errno = errno
        if self.errno == 0:
            self.error = "Unable to connect uArm"
        elif self.errno == 1:
            self.error = "Unknown Firmware Version"
        elif self.errno == 2:
            self.error = "Unsupported uArm Firmware Version"
        else:
            self.error = "Not Defined Error"

    def __str__(self):
        return repr(self.error + "-" + self.message)


# ################################### Other ################################

def progressbar(title, cur, total):
    percent = '{:.2%}'.format(cur / total)
    print(title + "[%-50s] %s" % (
                            '=' * int(math.floor(cur * 50 / total)),
                            percent), end='\r')