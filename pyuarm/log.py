from __future__ import print_function
from logging import DEBUG, ERROR, INFO
import sys
from . import PY3
import logging
from .version import __version__

# ################################### Log ################################
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
    if not logger.handlers:
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
    if not stream_logger.handlers:
        my_formatter = logging.Formatter('%(message)s')
        stream_logger.setLevel(logging.DEBUG)
        sch = logging.StreamHandler()
        sch.setFormatter(my_formatter)
        if PY3:
            sch.terminator = ""
        sch.setLevel(logging.DEBUG)
        stream_logger.addHandler(sch)


def close_logger():
    if pylogger is not None:
        handlers = pylogger.handlers
        for p in handlers:
            p.close()
            pylogger.removeHandler(p)
    if stream_logger is not None:
        handlers = stream_logger.handlers
        for p in handlers:
            p.close()
            stream_logger.removeHandler(p)


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
