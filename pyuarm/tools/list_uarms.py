from serial.tools import list_ports

UARM_HWID_KEYWORD = "USB VID:PID=0403:6001"


def uarm_ports():
    uarm_ports = []
    for i in list_ports.comports():
        if i.hwid[0:len(UARM_HWID_KEYWORD)] == UARM_HWID_KEYWORD:
            uarm_ports.append(i[0])
    return uarm_ports


def check_port_plug_in(serial_id):
    ports = list_ports.comports()
    for p in ports:
        if p.serial_number == serial_id:
            return True
    return False


def get_uarm_port_cli():
    uarm_list = uarm_ports()
    ports = uarm_ports()
    if len(ports) > 1:
        i = 1
        for port in ports:
            print("[{}] - {}".format(i, port))
            i += 1
        port_index = input("Please Choose the uArm Port: ")
        uarm_port = ports[int(port_index) - 1]
        return uarm_port
    elif len(ports) == 1:
        return uarm_list[0]
    elif len(ports) == 0:
        return None


def get_port_property(port_name):
    for p in list_ports.comports():
        if p.device == port_name:
            return p
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
        print(p)
    print("{0} ports found".format(len(ports)))


if __name__ == '__main__':
    main()
