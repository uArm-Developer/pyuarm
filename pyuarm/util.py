import logging
from .version import __version__

ERROR = 2
INFO  = 1
DEBUG = 0

global pylogger

def get_default_logger(debug=False):
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
    return logger

def init_logger(logger):
    """
    initialize global logger
    :param debug: if True, Turn on the logger debug
    :return:
    """
    global pylogger
    pylogger = logger
    printf('pyuarm version: ' + __version__)

def printf(msg, type=INFO):
    """
    global print log function
    :param msg:
    :param type:
    :return:
    """
    if type == INFO:
        pylogger.info(msg)
    elif type == DEBUG:
        pylogger.debug(msg)
    elif type == ERROR:
        pylogger.error(msg)


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