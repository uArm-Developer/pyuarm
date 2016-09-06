from serial.tools import list_ports
import pyuarm

UARM_HWID_KEYWORD = "USB VID:PID=0403:6001"


def uarm_ports():
    uarm_ports = []
    for i in list_ports.comports():
        if i.hwid[0:len(UARM_HWID_KEYWORD)] == UARM_HWID_KEYWORD:
            uarm_ports.append(i[0])
    return uarm_ports


def get_uarm_port_cli():
    uarm_list = uarm_ports()
    ports = uarm_ports()
    if len(ports) > 1:
        i = 1
        for port in ports:
            print ("[{}] - {}".format(i, port))
            i += 1
        port_index = raw_input("Please Choose the uArm Port: ")
        uarm_port = ports[int(port_index) - 1]
        return uarm_port
    elif len(ports) == 1:
        return uarm_list[0]
    elif len(ports) == 0:
        print ("No uArm ports is found.")
        return None


def get_uarm():
    """
    ===============================
    Get First uArm Port instance
    ===============================
    It will return the first uArm Port detected by **pyuarm.tools.list_uarms**,
    If no available uArm ports, will print *There is no uArm port available*

    .. raw:python
    >>> import pyuarm
    >>> uarm = pyuarm.get_uarm()
    There is no uArm port available


    :returns: uArm() Instance

    """
    ports = uarm_ports()
    if len(ports) > 0:
        return pyuarm.uArm(port=ports[0])
    else:
        print("There is no uArm port available")
        return None


def main():
    """
    ::

        $ python -m pyuarm.tools.list_uarms
        /dev/cu.usbserial-A600CVS9
        1 ports found

    """
    ports = uarm_ports()
    for p in ports:
        print (p)
    print ("{0} ports found".format(len(ports)))

if __name__ == '__main__':
    main()
