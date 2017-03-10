========
Examples
========

Usage
=====

Initialize uArm
---------------
There are two methods to Initialize uArm.

- Use get_uarm()

.. code-block:: python

    >>> import pyuarm
    >>> arm = pyuarm.get_uarm()
    pyuarm - INFO - pyuarm version: 2.4.0.7
    >>> arm.connect()
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRJU...

if no uArm connected, will return ``None`` and display "There is no uArm Port available"

.. code-block:: python

    >>> import pyuarm
    >>> arm = pyuarm.get_uarm()
    pyuarm - INFO - pyuarm version: 2.4.0.7
    pyuarm - ERROR - There is no uArm port available

- Use uArm()

.. code-block:: python

    >>> import pyuarm
    a>>> arm = pyuarm.UArm()
    pyuarm - INFO - pyuarm version: 2.4.0.7
    >>> arm.connect()
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRJU...


If no uArm connected, will raise ``UArmConnectException``.

.. code-block:: python

    >>> import pyuarm
    >>> arm = pyuarm.UArm()
    pyuarm - INFO - pyuarm version: 2.4.0.7
    >>> arm.connect()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pyuarm/uarm.py", line 112, in connect
        raise UArmConnectException(3)
    pyuarm.util.UArmConnectException: 'No available uArm Port-'


You could turn on Debug Mode

.. code-block:: python

    >>> import pyuarm
    >>> arm = pyuarm.UArm(debug=True)
    pyuarm - INFO - pyuarm version: 2.4.0.7
    >>> arm.connect()
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRJU...
    pyuarm - DEBUG - Received MSG: @1
    >>> arm.firmware_version
    pyuarm - DEBUG - #2 P203
    '2.2.1'
    >>> arm.hardware_version
    pyuarm - DEBUG - #3 P202
    '2.1'

Define the uArm port

.. code-block:: python

    >>> import pyuarm
    >>> arm = pyuarm.UArm(port_name='/dev/cu.usbserial-A600CRJU')
    pyuarm - INFO - pyuarm version: 2.4.0.7
    >>> arm.connect()
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRJU...

Connection
~~~~~~~~~~
Please connect before any operation or you will received exception

.. code-block:: python

    >>> import pyuarm
    >>> arm = pyuarm.UArm(port_name='/dev/cu.usbserial-A600CRJU')
    pyuarm - INFO - pyuarm version: 2.4.0.7
    >>> arm.set_pump(True)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "pyuarm/uarm.py", line 610, in set_pump
        self.__send_msg(command)
      File "pyuarm/uarm.py", line 311, in __send_msg
        raise UArmConnectException(4)
    pyuarm.util.UArmConnectException: 'uArm is not connected-'

Use connect()

.. code-block:: python

    >>> arm.connect()
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRJU...


Use disconnect(), Disconnect uArm and release the port

.. code-block:: python

    >>> arm.disconnect()
    pyuarm - ERROR - Receive Process Error - read failed: (9, 'Bad file descriptor')
    pyuarm - INFO - Disconnect from /dev/cu.usbserial-A600CRJU

* Because receive process in a different thread, so will raise Error, you could ignore it *

Please remember to use close() if program exit or finished

.. code-block:: python

    >>> arm.close()

Movement
~~~~~~~~

.. code-block:: python

    >>> arm.set_position(150, 150, 150) # Move to (150, 150, 150) at speed 300 mm/min
    >>> arm.set_position(150, 150, 150, speed=100) # Move to (150, 150, 150) at 100 mm/min
    >>> arm.set_position(x=20, speed=100, relative=True)  # Move (20, 0, 0) at 100 mm/min
    >>> arm.set_position(150, 150, 150, wait=True) # wait=True will block until uArm finish moving

Current Positions
~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> arm.get_position() # Get Current position, will return a position array
    [-2.74, 140.88, 151.0]


Pump Gripper control
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> arm.set_pump(True) ### Pump On
    >>> arm.set_pump(False) ### Pump
    >>> arm.set_pump(True, wait=True) # This will block until finish the pump
    >>> arm.set_gripper(True) # Same as Pump Control

Set Servo Attach/Detach
~~~~~~~~~~~~~~~~~~~~~~~
Servo Attach will lock the servo, You can't move uArm with your hands.

.. code-block:: python

    >>> arm.set_servo_attach() # This will attach all servos

    >>> from pyuarm import SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
    >>> arm.set_servo_attach(servo_num=SERVO_BOTTOM) # This will only attach SERVO_BOTTOM

    >>> arm.set_servo_attach(move=True) # if Move is True, servo will set will attach in current angle, if not, servo will set to last detach angle

    >>> arm.set_servo_attach(move=True, wait=True) # wait is True will block until finish moving


Servo Detach will unlock the servo, You can move uArm with your hands.

.. code-block:: python

    >>> arm.set_servo_detach() # This will detach all servos

    >>> from pyuarm import SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
    >>> arm.set_servo_detach(servo_num=SERVO_BOTTOM) # This will only detach SERVO_BOTTOM

    >>> arm.set_servo_detach(wait=True) # wait is True will block until finish detaching

Report Position
~~~~~~~~~~~~~~~
You could turn on a position report interval

.. code-block:: python

    >>> arm.set_report_position(0.2) # uArm will report current position in 0.2 sec
    >>> arm.set_servo_detach() # you could try with servo detach to watch the position
    >>> arm.get_report_position() # all position will store in a LIFO (Last In First Out) queue

Try to move uArm with below code

.. code-block:: python

    arm.set_servo_detach()
    start_time = time.time()
    while (time.time() - start_time) < 60:
        print (arm.get_report_position())

Close Report

.. code-block:: python

    >>> arm.close_report_position() # turn of position report
    >>> arm.set_report_position(0) # same as close report



Others
~~~~~~

- List uArm Ports

.. code-block:: python

    >>> from pyuarm.tools.list_uarms import uarm_ports
    >>> uarm_ports()
    ['/dev/cu.usbserial-A600CRE6']


