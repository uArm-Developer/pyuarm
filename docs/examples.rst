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
    Firmware Version: 1.5.9

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
    >>> uarm = pyuarm.uArm()
    Firmware Version: 1.5.9

If no uArm connected, will raise `NoUArmPortException`.

::

    >>> uarm = pyuarm.uArm()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pyuarm.py", line 114, in __init__
        raise NoUArmPortException()
    pyuarm.NoUArmPortException

You could turn on Debug Mode

::

    >>> import pyuarm
    >>> uarm = pyuarm.uArm(debug=True)
    f0aa23f7
    Firmware Version: 1.5.9

Define the uArm port

::

    >>> import pyuarm
    >>> uarm = pyuarm.uArm(port='/dev/cu.usbserial-A600CVS1')
    Firmware Version: 1.5.9

Movement
~~~~~~~~

::

    >>> uarm.moveTo(15, -5, 15) ### Absolute coordinate in 2 seconds
    >>> uarm.move(5, 5, 5) ### Relative coordinate

Current Positions
~~~~~~~~~~~~~~~~~

::

    >>> uarm.read_coordinate() ### Read Current Coordinate


Pump control
~~~~~~~~~~~~

::

    >>> uarm.pump_control(True) ### Pump On
    >>> uarm.pump_control(False) ### Pump Off


Others
~~~~~~

- List uArm Ports

::

    >>> import pyuarm
    >>> pyuarm.list_uarms() #List All available uArm Ports
    [u'/dev/cu.usbserial-A600CVS1']

