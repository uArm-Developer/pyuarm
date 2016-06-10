from serial.tools import list_ports

UARM_HWID_KEYWORD = "USB VID:PID=0403:6001"

def uarm_ports():
    uarm_ports = []
    for i in list_ports.comports():
        if i.hwid[0:len(UARM_HWID_KEYWORD)] == UARM_HWID_KEYWORD:
            uarm_ports.append(i[0])
    return uarm_ports

def main():
    ports = uarm_ports()
    for p in ports:
        print (p)
    print ("{0} ports found".format(len(ports)))

if __name__ == '__main__':
    main()
