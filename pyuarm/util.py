from __future__ import division
from __future__ import print_function
import math
from .tools.list_uarms import uarm_ports
from .log import printf, close_logger, ERROR
from .uarm import UArm

# Get UArm Instance


def get_uarm(debug=False,logger=None):
    """
    Get First uArm Port instance
    It will return the first uArm Port detected by **pyuarm.tools.list_uarms**,
    If no available uArm ports, will print *There is no uArm port available* and return None
    .. raw:python
    >>> import pyuarm
    >>> uarm = pyuarm.get_uarm()
    There is no uArm port available
    :returns: uArm() Instance

    """
    ports = uarm_ports()
    if len(ports) > 0:
        return UArm(port_name=ports[0], logger=logger, debug=debug)
    else:
        printf("There is no uArm port available", ERROR)
        close_logger()
        return None

# ################################### Other ################################


def progressbar(title, cur, total):
    percent = '{:.2%}'.format(cur / total)
    print(title + "[%-50s] %s" % (
                            '=' * int(math.floor(cur * 50 / total)),
                            percent), end='\r')
