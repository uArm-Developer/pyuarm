from __future__ import print_function
import serial
import time
import binascii
from util import *

# version
MAJOR_VERSION = 1
MINOR_VERSION = 3
BUGFIX_VERSION = 4
VERSION = str(MAJOR_VERSION) + "." + str(MINOR_VERSION) + "." + str(BUGFIX_VERSION)
version = VERSION
__version__ = version

class uArm(object):
    """
    **uArm** class is let you make an instance for uArm.

    eg.

    ::

        >>> import pyuarm
        >>> uarm = pyuarm.uArm()
        Initialize uArm, port is /dev/cu.usbserial-A600CVS1...
        Firmware Version: 1.5.11

    :param port: uArm Port name, Default is **None**

    :param debug: Debug Mode Control Flag, If debug is **True**, Will display all in/out serial message(in Hex Format)

    :param timeout: Serial Timeout parameter, Default is **5** Seconds.

    :raise NoUArmPortException: No uArm available
    :raise UnkwonFirmwareException: Not unrecognized firmware version
    """
    firmware_version = "0.0.0"
    firmata_version = "0.0"

    def __init__(self, port=None, debug=False, timeout=5):

        if port is None:
            ports = uarm_ports()
            if len(ports) > 0:
                port = ports[0]
            else:
                raise NoUArmPortException("No uArm is connected.")
        self.port = port
        self.debug = debug
        print("Initialize uArm, port is {0}...".format(self.port))
        self.sp = serial.Serial(port, baudrate=57600, timeout=timeout)
        try:
            self.set_firmata_version()
            self.set_frimware_version()
        except serial.SerialException as e:
            raise UnkwonFirmwareException(
                "Unkwon Firmware Version, Please use 'pyuarm.tools.firmware_helper' upgrade your firmware")
        except TypeError as e:
            raise UnkwonFirmwareException(
                "Unkwon Firmware Version, Please use 'pyuarm.tools.firmware_helper' upgrade your firmware")
        print("Firmware Version: {0}".format(self.firmware_version))

    def is_connected(self):
        """
        This function will detect if uArm is connected

        :returns: True - Connected, False - Disconnected
        """
        if not self.sp.isOpen():
            return False
        else:
            return True

    def disconnect(self):
        """
        Close serial connection and release the uArm Port.
        """
        self.sp.close()

    def reconnect(self):
        """
        Reconnect serial connection with uArm Port.
        """
        if not self.is_connected():
            self.sp.open()
            self.set_firmata_version()
            self.set_frimware_version()

    def set_firmata_version(self):
        """
        Read frimata version after initialize the uArm.
        """
        while self.sp.readable():
            readData = self.serial_read_byte()
            if readData == END_SYSEX:
                break
            if readData == START_SYSEX:
                readData = self.serial_read_byte()
                if readData == REPORT_FIRMATA_VERSION:
                    frimata_major_version = self.serial_read_byte()
                    frimata_minor_version = self.serial_read_byte()
                    self.firmata_version = str(frimata_major_version) + "." + str(frimata_minor_version)

    def read_servo_angle(self, servo_number, with_offset=True):
        """
        Read Servo Angle

        eg.

        ::

            >>> import pyuarm
            >>> uarm = pyuarm.uArm(debug=True)
            Initialize uArm, port is /dev/cu.usbserial-A600CRCD...
            f925Serial Read: f079135504107206d04606907206d06107406102e06906e06f0f7
            Serial Write:f0aa23f7
            Serial Read: f0aa2315bf7
            Firmware Version: 1.5.11
            >>> uarm.read_servo_angle(pyuarm.SERVO_BOTTOM)
            Serial Write:f0aa100001f7
            Serial Read: f0aa05c034f7
            92.52
            >>> uarm.read_servo_angle(pyuarm.SERVO_BOTTOM,False)
            Serial Write:f0aa100000f7
            Serial Read: f0aa058015f7
            88.21

        :param servo_number:    SERVO_BOTTOM
                                SERVO_LEFT
                                SERVO_RIGHT
                                SERVO_RIGHT
        :param with_offset: default - True

        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_ANGLE])
        msg.extend(getValueAsOne7bitBytes(servo_number))

        msg.extend(getValueAsOne7bitBytes(1 if with_offset else 0))
        msg.append(END_SYSEX)
        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read_byte()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read_byte()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read_byte()
                    while read_byte != END_SYSEX:
                        received_data.append(read_byte)
                        read_byte = self.serial_read_byte()
                    if received_data[0] == servo_number:
                        return received_data[2] * 128 + received_data[1] + received_data[3] / 100.00

    def read_eeprom(self, data_type, eeprom_address):
        """
        Read data from EEPROM
        =====================
        Byte: 1 Byte

        Integer: 2 Bytes

        Float: 4 Bytes

        Please reference Arduino EEPROMGet_.

        .. _EEPROMGet: https://www.arduino.cc/en/Reference/EEPROMGet

        :param data_type:   EEPROM_DATA_TYPE_BYTE

                            EEPROM_DATA_TYPE_FLOAT

                            EEPROM_DATA_TYPE_INTEGER

        :param eeprom_address: EEPROM Address
        :returns: byte, integer, float
        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_EEPROM])
        msg.append(data_type)
        msg.extend(getValueAsTwo7bitBytes(eeprom_address))
        msg.append(END_SYSEX)

        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read_byte()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read_byte()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read_byte()
                    if read_byte == READ_EEPROM:
                        read_byte = self.serial_read_byte()
                        while read_byte != END_SYSEX:
                            received_data.append(read_byte)
                            read_byte = self.serial_read_byte()
                        res_eeprom_add = received_data[1] * 128 + received_data[0]
                        if res_eeprom_add == eeprom_address:
                            if data_type == EEPROM_DATA_TYPE_BYTE:
                                return (received_data[3] << 7) + received_data[2]
                            if data_type == EEPROM_DATA_TYPE_FLOAT:
                                val = (received_data[4] << 7) + received_data[3] + float(received_data[5]) / 100.00
                                val = val if received_data[2] == 0 else -val
                                return val
                            if data_type == EEPROM_DATA_TYPE_INTEGER:
                                val = (received_data[4] << 7) + received_data[3]
                                val = val if received_data[2] == 0 else -val
                                return val

    def read_digital(self, pin_num, pin_mode):
        """
        Read Digital from PIN
        =====================
        Please reference Arduino DigitalPINs_.
        .. _DigitalPINs: https://www.arduino.cc/en/Tutorial/DigitalPins

        :param pin_num: Integer 1 to 13
        :param pin_mode: PULL_UP, INPUT
        :returns: Digital Value - HIGH, LOW

        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_DIGITAL])
        msg.extend(getValueAsOne7bitBytes(pin_num))
        msg.extend(getValueAsOne7bitBytes(pin_mode))
        msg.append(END_SYSEX)

        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read_byte()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read_byte()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read_byte()
                    while read_byte != END_SYSEX:
                        received_data.append(read_byte)
                        read_byte = self.serial_read_byte()
                    if received_data[0] == pin_num:
                        return received_data[1]

    def read_analog(self, pin_num):
        """
        Read Analog from PIN
        ====================
        Please reference Arduino AnalogRead_.
        .. _AnalogRead: https://www.arduino.cc/en/Reference/AnalogRead

        :param pin_num: Integer 1 to 13
        :returns: Analog Value - Integer

        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_ANALOG])
        msg.extend(getValueAsOne7bitBytes(pin_num))
        msg.append(END_SYSEX)
        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read_byte()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read_byte()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read_byte()
                    while read_byte != END_SYSEX:
                        received_data.append(read_byte)
                        read_byte = self.serial_read_byte()
                    if received_data[0] == pin_num:
                        return received_data[2] * 128 + received_data[1]

    def read_coordinate(self, pin_num):
        """

        :param pin_num:

        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_COORDS])
        msg.extend(getValueAsOne7bitBytes(pin_num))
        msg.append(END_SYSEX)
        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read_byte()
            received_data = []
            coords = []
            coords_val = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read_byte()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read_byte()
                    while read_byte != END_SYSEX:
                        received_data.append(read_byte)
                        read_byte = self.serial_read_byte()
                    for i in range(0, 3):
                        coords_sign = (received_data[i * 4] == 1 and -1 or 1)
                        if i == 1 or i == 2:
                            coords_sign = -coords_sign
                        coords_val = received_data[2 + 4 * i] * 128 + received_data[1 + 4 * i] + received_data[
                                                                                                     3 + 4 * i] / 100.00
                        coords.append(coords_sign * coords_val)
                    return coords

    def write_eeprom(self, data_type, eeprom_add, eeprom_val):
        """
        Write Data to EEPROM
        ====================
        Please reference Arduino EEPROMPut_.
        :: _EEPROMPut: https://www.arduino.cc/en/Reference/EEPROMPut
        :param data_type: EEPROM_TYPE_BYTE, EEPROM_TYPE_INTEGER, EEPROM_TYPE_FLOAT
        :param eeprom_add: EEPROM address Integer
        :param eeprom_val: EEPROM Value - Byte, Integer, Float

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_EEPROM, data_type])
        msg.extend(getValueAsTwo7bitBytes(eeprom_add))
        if data_type == EEPROM_DATA_TYPE_BYTE:
            msg.extend(getValueAsTwo7bitBytes(eeprom_val))
        if data_type == EEPROM_DATA_TYPE_FLOAT:
            msg.extend(getFloatAsFour7bitBytes(eeprom_val))
        if data_type == EEPROM_DATA_TYPE_INTEGER:
            msg.extend(getIntegerAsThree7bitBytes(eeprom_val))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_analog(self, pin_number, pin_value):
        """
        Write Analog to PIN
        ====================
        Please reference Arduino AnalogWrite_.
        :: _AnalogWrite: https://www.arduino.cc/en/Reference/AnalogWrite
        :param pin_number: PIN Number Integer 0 - 13
        :param pin_value: Analog Value

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_ANALOG])
        msg.extend(getValueAsOne7bitBytes(pin_number))
        msg.extend(getValueAsTwo7bitBytes(pin_value))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_digital(self, pin_number, pin_mode):
        """
        Write Digital to PIN
        ====================
        Please reference Arduino DigitalWrite_.
        :: _DigitalWrite: https://www.arduino.cc/en/Reference/DigitalWrite
        :param pin_number: PIN Number - Integer 0~13
        :param pin_mode: Digital Value - HIGH, LOW

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_DIGITAL])
        msg.extend(getValueAsOne7bitBytes(pin_number))
        msg.extend(getValueAsOne7bitBytes(pin_mode))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def detach_all_servos(self):
        """
        Detach All Servos
        =================
        Unlock the servo after detach.
        """
        msg = bytearray([START_SYSEX, UARM_CODE, DETACH_SERVO, END_SYSEX])
        self.serial_write(msg)

    def write_servo_angle(self, servo_number, servo_angle, with_offset):
        """
        Write Servo Angle
        =================

        :param servo_number: SERVO_BUTTON_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_NUM
        :param servo_angle: float type - 0.00 ~ 180.00
        :param with_offset: True, False

        """
        servo_number = int(servo_number)
        servo_angle = float(servo_angle)
        with_offset = int(with_offset)
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_ANGLE])
        msg.extend(getValueAsOne7bitBytes(servo_number))
        msg.extend(getFloatAsThree7bitBytes(servo_angle))
        msg.extend(getValueAsOne7bitBytes(with_offset))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_left_right_servo_angle(self, servo_left_angle, servo_right_angle, with_offset):
        """

        :param servo_left_angle:
        :param servo_right_angle:
        :param with_offset:

        """
        with_offset = int(with_offset)
        servo_left_angle = float(servo_left_angle)
        servo_right_angle = float(servo_right_angle)
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_LEFT_RIGHT_ANGLE])
        msg.extend(getFloatAsThree7bitBytes(servo_left_angle))
        msg.extend(getFloatAsThree7bitBytes(servo_right_angle))
        msg.extend(getValueAsOne7bitBytes(with_offset))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def move(self, x, y, z):
        """

        :param x:
        :param y:
        :param z:

        """
        x, y, z = float(x), float(y), float(z)
        self.move_to_options(x, y, z, 0, 1, 0, 0, 0)

    def move_to(self, x, y, z):
        """

        :param x:
        :param y:
        :param z:

        """
        x, y, z = float(x), float(y), float(z)
        self.move_to_options(x, y, z, 0, 0, 0, 0, 0)

    def pump_control(self, val):
        """

        :param val:

        """
        pump_status = 1 if val else 0
        msg = bytearray([START_SYSEX, UARM_CODE, PUMP_STATUS])
        msg.extend(getValueAsOne7bitBytes(pump_status))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def gripper_control(self, val):
        """

        :param val:

        """
        gripper_status = 1 if val else 0
        msg = bytearray([START_SYSEX, UARM_CODE, GRIPPER_STATUS])
        msg.extend(getValueAsOne7bitBytes(gripper_status))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def move_to_options(self, x, y, z, hand_angle, relative_flags, time_spend, path_type, ease_type):
        """

        :param x:
        :param y:
        :param z:
        :param hand_angle:
        :param relative_flags:
        :param time_spend:
        :param path_type:
        :param ease_type:

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_COORDS])
        msg.extend(getFloatAsFour7bitBytes(x))
        msg.extend(getFloatAsFour7bitBytes(y))
        msg.extend(getFloatAsFour7bitBytes(z))
        msg.extend(getFloatAsThree7bitBytes(hand_angle))
        msg.extend(getValueAsOne7bitBytes(relative_flags))
        msg.extend(getFloatAsThree7bitBytes(time_spend))
        msg.extend(getValueAsOne7bitBytes(path_type))
        msg.extend(getValueAsOne7bitBytes(ease_type))
        # msg.append(1 if enable_hand else 0)
        msg.append(END_SYSEX)
        time.sleep(0.01)
        self.serial_write(msg)

    def move_to_simple(self, x, y, z, hand_angle, relative_flags, time_spend):
        """

        :param x:
        :param y:
        :param z:
        :param hand_angle:
        :param relative_flags:
        :param time_spend:

        """
        self.move_to_options(x, y, z, hand_angle, relative_flags, time_spend, 0, 0)

    def write_stretch(self, length, height):
        """

        :param length:
        :param height:

        """
        length = float(length)
        height = float(height)
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_STRETCH])
        msg.extend(getFloatAsFour7bitBytes(length))
        msg.extend(getFloatAsFour7bitBytes(height))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_serial_number(self, serial_number):
        """

        :param serial_number:

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_SERIAL_NUMBER])
        for c in serial_number:
            msg.append(ord(c))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def read_serial_number(self):
        """ """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_SERIAL_NUMBER, END_SYSEX])
        self.serial_write(msg)
        while self.sp.readable():
            readData = self.serial_read_byte()
            received_data = []
            if (readData == START_SYSEX):
                readData = self.serial_read_byte()
                if (readData == UARM_CODE):
                    readData = self.serial_read_byte()
                    if (readData == READ_SERIAL_NUMBER):
                        readData = self.serial_read_byte()
                        while readData != END_SYSEX:
                            received_data.append(readData)
                            readData = self.serial_read_byte()
                        sn_array = []
                        for r in received_data:
                            sn_array.append(chr(r))
                        return ''.join(sn_array)

    def alert(self, times, run_time, stop_time):
        """

        :param times:
        :param run_time:
        :param stop_time:

        """
        msg = bytearray([START_SYSEX, UARM_CODE, BUZZER_ALERT, times, run_time, stop_time, END_SYSEX])
        self.serial_write(msg)

    def set_frimware_version(self):
        """ """
        if self.is_connected():
            msg = bytearray([START_SYSEX, UARM_CODE, REPORT_LIBRARY_VERSION, END_SYSEX])
            self.serial_write(msg)
            while self.sp.readable():
                readData = self.serial_read_byte()
                received_data = []
                if (readData == START_SYSEX):
                    readData = self.serial_read_byte()
                    if (readData == UARM_CODE):
                        readData = self.serial_read_byte()
                        if (readData == REPORT_LIBRARY_VERSION):
                            readData = self.serial_read_byte()
                            while readData != END_SYSEX:
                                received_data.append(readData)
                                readData = self.serial_read_byte()
                            firmware_major_version = received_data[0]
                            firmware_minor_version = received_data[1]
                            firmware_bugfix = received_data[2]
                            self.firmware_version = str(firmware_major_version) + "." + str(
                                firmware_minor_version) + "." + str(firmware_bugfix)
                            break
        else:
            print("uArm is not Connected")

    def serial_write(self, msg):
        """

        :param msg:

        """
        if self.debug:
            print("Serial Write:{0}".format(binascii.hexlify(msg)))
        self.sp.write(msg)

    def serial_read_byte(self):
        """ """
        read_byte = ord(self.sp.read(1))
        if self.debug:
            if read_byte == START_SYSEX:
                print ("Serial Read:", end=' ')
            print(format(read_byte, 'x'), end='')
            if read_byte == END_SYSEX:
                print("")
        return read_byte
