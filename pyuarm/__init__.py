import sys
if sys.version > '3':
    PY3 = True
else:
    PY3 = False
from .uarm import UArm, get_uarm
from .version import __version__
from .util import set_debug