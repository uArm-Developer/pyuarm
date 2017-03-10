=====
Tools
=====

pyuarm provides some tools for developer.

- list_uarms, you could filter the uArm Ports from system easily

::

    $python -m pyuarm.tools.list_uarms
    /dev/cu.usbserial-A600CRJU
    1 ports found

Here is the example use in code. It will return the first port scanned in your system.

.. code-block:: python

    def get_uarm():
        ports = uarm_ports()
        if len(ports) > 0:
            return UArm(port_name=ports[0])
        else:
            return None

- firmware, you could flash the firmware and download the latest firmware

::

    $python -m pyuarm.tools.firmware -d
    pyuarm - INFO - pyuarm version: 2.4.0.9
    pyuarm - INFO - writing to /Users/alex/uarm/assistant/firmware.hex, file size: 80486 bytes
    Downloading: [==================================================] 100.00%
    pyuarm - INFO - Flash Command:
    avrdude -patmega328p -carduino -P/dev/cu.usbserial-A600CRJU -b115200 -D -Uflash:w:/Users/alex/uarm/assistant/firmware.hex:i
    Flashing: [==================================================] 100.00%


- calibrate, query calibrate information

::

    $python -m pyuarm.tools.calibrate
    pyuarm - INFO - pyuarm version: 2.4.0.9
    pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRJU...
    pyuarm - INFO - All Calibration: COMPLETED
    pyuarm - INFO - Linear Calibration: COMPLETED
    pyuarm - INFO - Manual Calibration: COMPLETED
    pyuarm - INFO - Servo 0 INTERCEPT: -29.7, SLOPE: 0.35, MANUAL: -20.84
    pyuarm - INFO - Servo 1 INTERCEPT: -28.41, SLOPE: 0.34, MANUAL: 5.0
    pyuarm - INFO - Servo 2 INTERCEPT: -30.68, SLOPE: 0.35, MANUAL: -11.0
    pyuarm - INFO - Servo 3 INTERCEPT: -45.37, SLOPE: 0.51, MANUAL: 0.0



You could use this summary script

``uarmcli -h`` or ``python -m pyuarm.tools.scripts -h``

::

    $python -m pyuarm.tools.scripts -h
    usage: scripts.py [-h] [-v] {miniterm,calibrate,list,firmware} ...

    positional arguments:
      {miniterm,calibrate,list,firmware}

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit


::

    $python -m pyuarm.tools.scripts list
    /dev/cu.usbserial-A600CRJU
    1 ports found

::

    python -m pyuarm.tools.scripts firmware -h
    usage: scripts.py firmware [-h] [-p PORT] [--path PATH] [--debug] [-d]

    optional arguments:
      -h, --help            show this help message and exit
      -p PORT, --port PORT  specify port number
      --path PATH           firmware path
      --debug               Turn on Debug Mode
      -d, --download        download firmware online

