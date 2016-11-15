import logging
from .version import __version__

ERROR = 2
INFO  = 1
DEBUG = 0

def init_logger(debug):
    """
    initialize global logger
    :param debug: if True, Turn on the logger debug
    :return:
    """
    logger = logging.getLogger('pyuarm')
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    # #
    ch = logging.StreamHandler()
    # # # if debug:
    # # #     ch.setLevel(logging.DEBUG)
    # # # else:
    # # #     ch.setLevel(logging.INFO)
    # ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('pyuarm version: ' + __version__)


def printf(msg, type=INFO):
    """
    global print log function
    :param msg:
    :param type:
    :return:
    """
    if type == INFO:
        logging.getLogger('pyuarm').info(msg)
    elif type == DEBUG:
        logging.getLogger('pyuarm').debug(msg)
    elif type == ERROR:
        logging.getLogger('pyuarm').debug(msg)


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