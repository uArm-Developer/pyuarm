===============================
Examples
===============================


Usage
=====

Initialize uArm
---------------
There are two methods to Initialize uArm.

- Use get_uarm()

::

    >>> import pyuarm
    >>> uarm = pyuarm.get_uarm()
    Firmware Version: 2.1.4

if no uArm connected, will return `None` and display "There is no uArm Port available"

::

    >>> import pyuarm
    >>> uarm = pyuarm.get_uarm()
    There is no uArm port available
    >>> print uarm
    None

- Use uArm()

::

    >>> import pyuarm
    >>> uarm = pyuarm.UArm()
    Firmware Version: 2.1.4

If no uArm connected, will raise `UArmConnectException`.

::

    >>> uarm = pyuarm.UArm()
    pyuarm - INFO - pyuarm version: 2.1.1
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/Users/alex/Worksapce/project/metal/python/pyuarm/pyuarm/uarm.py", line 35, in __init__
        raise UArmConnectException(0, "No uArm ports is found.")
    pyuarm.util.UArmConnectException: 'Unable to connect uArm-No uArm ports is found.'

You could turn on Debug Mode

::

    >>> uarm = pyuarm.UArm(debug=True)
    pyuarm - INFO - pyuarm version: 2.1.1
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRE6...
    pyuarm - INFO - connected...
    pyuarm - DEBUG - Communication| [gVer]                           [SH2-2.1.4]
    pyuarm - INFO - Firmware Version: 2.1.4
Define the uArm port

::

    >>> uarm = pyuarm.UArm(port_name='/dev/cu.usbserial-A600CRE6')
    pyuarm - INFO - pyuarm version: 2.1.1
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRE6...
    pyuarm - INFO - connected...
    pyuarm - INFO - Firmware Version: 2.1.4

Movement
~~~~~~~~

::

    >>> uarm.set_position(150, 150, 150) #default speed is 300 mm/sec
    >>> uarm.set_position(150, 150, 150, 100) ### set position in 100 mm/sec

Current Positions
~~~~~~~~~~~~~~~~~

::

    >>> uarm.get_position() # Get Current position
    [354.62, 0.0, 90.0]
Pump control
~~~~~~~~~~~~

::

    >>> uarm.set_pump(True) ### Pump On
    >>> uarm.set_pump(False) ### Pump Off


Others
~~~~~~

- List uArm Ports

::

    >>> from pyuarm.tools.list_uarms import uarm_ports
    >>> uarm_ports()
    ['/dev/cu.usbserial-A600CRE6']
