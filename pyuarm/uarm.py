from __future__ import print_function
import serial
from . import version, protocol, util
from .util import *
from .tools.list_uarms import uarm_ports, get_port_property, check_port_plug_in
from . import PY3
import time
import threading

if PY3:
    from queue import Queue, LifoQueue, Empty
else:
    from Queue import Queue, LifoQueue, Empty


def get_uarm(logger=None):
    """
    ===============================
    Get First uArm Port instance
    ===============================
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
        return UArm(port_name=ports[0], logger=logger)
    else:
        printf("There is no uArm port available", ERROR)
        return None


class UArm(object):
    def __init__(self, port_name=None, timeout=2, debug=False, logger=None):
        """
        :param port_name: UArm Serial Port name, if no port provide, will try first port we detect
        :param logger: if no logger provide, will create a logger by default
        :param debug: if Debug is True, create a Debug Logger by default
        :param timeout: default timeout is 5 sec.
        :raise UArmConnectException

        if no port provide, we will detect all connected uArm serial devices.
        please reference `pyuarm.tools.list_uarms`
        port is a device name: depending on operating system.
        eg. `/dev/ttyUSB0` on GNU/Linux or `COM3` on Windows.
        logger will display all info/debug/error/warning messages.
        """
        self.timeout = timeout
        if port_name is not None:
            self.port_name = port_name
        if logger is None:
            set_default_logger(debug)
        else:
            init_logger(logger)
        self.port_name = None
        self.__data_buf = None
        self.__position_queue = None
        self.__menu_button_queue = None
        self.__play_button_queue = None
        self.__send_queue = None
        self.__firmware_version = None
        self.__hardware_version = None
        self.__isReady = None
        self.__receive_thread = None
        self.__send_thread = None
        self.serial_id = None
        self.msg_buff = None
        self.__serial = None
        self.__reader_thread = None
        self.__transport = None
        self.__protocol = None
        self.port = None
        self.__connected = None

    def __init_serial_core(self):
        if PY3:
            from .threaded import UArmSerial, UArmReaderThread
            self.__reader_thread = UArmReaderThread(self.__serial, UArmSerial, self.__data_buf)
            self.__reader_thread.start()
            self.__reader_thread.connect()
            self.__transport, self.__protocol = self.__reader_thread.connect()
        else:
            self.__connected = True

    def __close_serial_core(self):
        if PY3:
            self.__reader_thread.stop()
        else:
            self.__connected = False

    def connect(self):
        """
        This function will open the port immediately. Function will wait for the READY Message for 5 secs. Once received
        READY message, Function will send the Version search command.
        :return:
        """
        if self.port_name is None:
            ports = uarm_ports()
            if len(ports) > 0:
                self.port_name = ports[0]
            else:
                raise UArmConnectException(3)
        self.__data_buf = []
        self.__position_queue = LifoQueue()
        self.__menu_button_queue = LifoQueue()
        self.__play_button_queue = LifoQueue()
        self.__send_queue = Queue()
        self.__firmware_version = None
        self.__hardware_version = None
        self.__isReady = False
        self.port = get_port_property(self.port_name)
        self.__receive_thread = threading.Thread(target=self.__receive_thread_process)
        self.__send_thread = threading.Thread(target=self.__send_thread_process)
        self.__receive_thread.setDaemon(True)
        self.__send_thread.setDaemon(True)
        self.serial_id = 1
        self.msg_buff = {}
        self.__serial = serial.Serial(baudrate=115200, timeout=0.1)
        try:
            self.__serial.port = self.port.device
            printf("Connecting from port - {0}...".format(self.port.device))
            self.__serial.open()
            self.__init_serial_core()
            self.__connect()
        except serial.SerialException as e:
            raise UArmConnectException(0, "port: {}, Error: {}".format(self.port.device, e.strerror))

    def __connect(self):
        start_time = time.time()
        while time.time() - start_time < 5:
            if self.is_connected():
                break
        self.__receive_thread.start()
        self.__send_thread.start()
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.__isReady:
                break

    def is_connected(self):
        if PY3:
            if self.__protocol is not None:
                return self.__protocol.get_connect_status()
            else:
                return False
        else:
            if self.__serial is not None:
                return self.__serial.is_open and self.__connected
            else:
                return False

    def disconnect(self):
        """
        Disconnect the serial connection, terminate all queue and thread
        :return:
        """
        self.__close_serial_core()
        self.__serial.close()
        printf("Disconnect from {}".format(self.port_name))

    def __process_line(self, line):
        if line is not None:
            if line.startswith("$"):
                values = line.split(' ')
                msg_id = int(values[0].replace('$', ''))
                self.msg_buff[msg_id] = values[1:]
            elif line.startswith(protocol.READY):
                printf("Received MSG: {}".format(line), DEBUG)
                self.__isReady = True
            elif line.startswith(protocol.REPORT_POSITION_PREFIX):
                printf("POSITION REPORT: {}".format(line), DEBUG)
                values = line.split(' ')
                pos_array = [float(values[1][1:]), float(values[2][1:]),
                             float(values[3][1:]), float(values[4][1:])]
                self.__position_queue.put(pos_array, block=False)
            # elif line.startswith(protocol.REPORT_BUTTON_PRESSED):
            #     printf("BUTTON REPORT: {}".format(line), DEBUG)
            #     values = line.split(' ')
            #     if values[1] == protocol.BUTTON_MENU:
            #         self.__menu_button_queue.put(values[2][1:])
            #     elif values[1] == protocol.BUTTON_PLAY:
            #         self.__play_button_queue.put(values[2][1:])

    def __receive_thread_process(self):
        """
        this Function is for receiving thread function, All serial response message would store in __receive_queue.
        This thread will be finished if serial connection is end.
        :return:
        """
        while self.is_connected():
            try:
                line = None
                if PY3:
                    if len(self.__data_buf) > 0:
                        line = self.__data_buf.pop()
                else:
                    line = self.__serial.readline()
                    if not line:
                        continue
                self.__process_line(line)
            except serial.SerialException as e:
                printf("Receive Process Error {} - {}".format(e.errno, e))
                if PY3:
                    self.__connected = False
            except Exception as e:
                printf("Error: {}".format(e), ERROR)
            time.sleep(0.001)
        # Make Sure all queues were release
        self.__position_queue.join()
        self.__play_button_queue.join()
        self.__menu_button_queue.join()

    def __send_thread_process(self):
        """
        this function is for sending thread function, All serial writable function should be through this thread,
        thread will be finished if serial connection is end.
        :return:
        """
        while self.is_connected():
            try:
                item = self.__send_queue.get()
                if item is None:
                    break
                msg_id = item['id']
                msg_content = item['msg']
                msg = '#{} {}'.format(msg_id, msg_content)
                if PY3:
                    self.__protocol.write_line(msg)
                else:
                    self.__serial.write(msg)
                    self.__serial.write('\n')
                printf(msg, DEBUG)
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if msg_id in self.msg_buff.keys():
                        break
                self.__send_queue.task_done()
            except Exception as e:
                printf("Error: {}".format(e), ERROR)
            time.sleep(0.001)
        # Make Sure all queues were release
        self.__send_queue.join()

    def __gen_serial_id(self):
        """
        Generate a serial id to identify the item.
        :return:
        """
        if self.serial_id == 65535:
            self.serial_id = 1
        else:
            self.serial_id += 1
        return self.serial_id

    def send_and_receive(self, msg):
        """

        :param msg:
        :return:
        :return:
        """
        if self.is_connected():
            msg_id = self.__gen_serial_id()
            item = {'id': msg_id, 'msg': msg}
            self.__send_queue.put(item)
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if msg_id in self.msg_buff.keys():
                    return msg_id, self.msg_buff[msg_id]
            # print("duration: {}".format(time.time() - start_time))
            return None
        else:
            printf("No uArm connect", ERROR)

    def __send_msg(self, msg):
        """

        :param msg:
        :return:
        """
        if self.is_connected():
            serial_id = self.__gen_serial_id()
            _msg = '#{} {}'.format(serial_id, msg)
            if PY3:
                self.__protocol.write_line(_msg)
            else:
                self.__serial.write(_msg)
                self.__serial.write('\n')
            printf("Send #{} {}".format(serial_id, msg), DEBUG)
            return serial_id
        else:
            printf("No uArm connect", ERROR)

# -------------------------------------------------------- Commands ---------------------------------------------------#

    def reset(self):
        """
        reset to default position
        :return:
        """
        self.set_servo_attach()
        time.sleep(0.1)
        self.set_position(0, 150, 150, speed=100)
        self.set_pump(False)
        self.set_wrist(90)

# -------------------------------------------------------- Get Commands -----------------------------------------------#
    @property
    def firmware_version(self):
        """
        Get the firmware version.
        Protocol Cmd: `protocol.GET_FIRMWARE_VERSION`
        :return: firmware version, if failed return False
        """
        if self.__firmware_version is not None:
            return self.__firmware_version
        else:
            try:
                cmd = protocol.GET_FIRMWARE_VERSION
                serial_id, response = self.send_and_receive(cmd)
                if response is not None:
                    if response[0] == protocol.OK:
                        self.__firmware_version = response[1].replace('V', '')
                        return self.__firmware_version
                return None
            except Exception as e:
                printf("Error: {}".format(e), ERROR)

    @property
    def hardware_version(self):
        """
        Get the Product version.
        Protocol Cmd: `protocol.GET_HARDWARE_VERSION`
        :return: firmware version, if failed return False
        """
        if self.__hardware_version is not None:
            return self.__hardware_version
        else:
            try:
                cmd = protocol.GET_HARDWARE_VERSION
                serial_id, response = self.send_and_receive(cmd)
                if response is not None:
                    if response[0] == protocol.OK:
                        self.__hardware_version = response[1].replace('V', '')
                        return self.__hardware_version
                return None
            except Exception as e:
                printf("Error: {}".format(e), ERROR)

    def get_position(self):
        """
        Get Current uArm position (x,y,z) mm
        :return: Returns an array of the format [x, y, z] of the robots current location
        """
        try:
            serial_id, response = self.send_and_receive(protocol.GET_COOR)
            if response is None:
                printf("No Message response {}".format(serial_id), ERROR)
                return None
            if response[0] == protocol.OK:
                x = float(response[1][1:])
                y = float(response[2][1:])
                z = float(response[3][1:])
                coordinate = [x, y, z]
                return coordinate
            return None
        except Exception as e:
            printf("Error {}".format(e), ERROR)
            return None

    def get_is_moving(self):
        """
        Get is uArm Moving
        :return: True or False
        """
        try:
            serial_id, response = self.send_and_receive(protocol.GET_IS_MOVE)
            if response is None:
                printf("No Message response {}".format(serial_id), ERROR)
                return None
            if response[0] == protocol.OK:
                v = int(response[1][1:])
                if v == 0:
                    return False
                elif v == 1:
                    return True
        except Exception as e:
            printf("Error {}".format(e), ERROR)
            return None

    def get_polar(self):
        """
        get Polar coordinate
        :return: Return an array of the format [rotation, stretch, height]
        """
        try:
            serial_id, response = self.send_and_receive(protocol.GET_POLAR)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return
            if response[0] == protocol.OK:
                stretch = float(response[1][1:])
                rotation = float(response[2][1:])
                height = float(response[3][1:])
                polar = [rotation, stretch, height]
                return polar
            else:
                return None
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_tip_sensor(self):
        """
        Get Status from Tip Sensor
        :return: True On/ False Off
        """
        try:
            serial_id, response = self.send_and_receive(protocol.GET_TIP_SENSOR)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return
            if response[0] == protocol.OK:
                if response[1] == 'V0':
                    return True
                elif response[1] == 'V1':
                    return False
            else:
                return None
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_servo_angle(self, servo_num=None):
        """
        Get Servo Angle
        :param servo_num: if servo_num not provide, will return a array. for all servos, servo 0
        , servo 1, servo 2, servo 3
        :return:
        """
        try:
            serial_id, response = self.send_and_receive(protocol.GET_SERVO_ANGLE)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                servo_0 = float(response[1][1:])
                servo_1 = float(response[2][1:])
                servo_2 = float(response[3][1:])
                servo_3 = float(response[4][1:])
                servo_array = [servo_0, servo_1, servo_2, servo_3]
                if servo_num is None:
                    return servo_array
                elif servo_num == 0:
                    return servo_0
                elif servo_num == 1:
                    return servo_1
                elif servo_num == 2:
                    return servo_2
                elif servo_num == 3:
                    return servo_3
            else:
                return None
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_analog(self, pin):
        """
        Get Analog Value from specific PIN
        :param pin:
        :return:
        """
        try:
            cmd = protocol.GET_ANALOG.format(pin)
            serial_id, response = self.send_and_receive(cmd)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return
            if response[0] == protocol.OK:
                val = "".join(response[1:])[1:]
                return int(float(val))
            else:
                return None
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_digital(self, pin):
        """
        Get Digital Value from specific PIN.
        :param pin:
        :return:
        """
        try:
            cmd = protocol.GET_DIGITAL.format(pin)
            serial_id, response = self.send_and_receive(cmd)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return
            if response[0] == protocol.OK:
                if response[1] == 'V0':
                    return True
                elif response[1] == 'V1':
                    return False
            else:
                return None
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_rom_data(self, address, data_type=protocol.EEPROM_DATA_TYPE_BYTE):
        """
        Get DATA From EEPROM
        :param address: 0 - 2048
        :param data_type: EEPROM_DATA_TYPE_FLOAT, EEPROM_DATA_TYPE_INTEGER, EEPROM_DATA_TYPE_BYTE
        :return:
        """
        try:
            cmd = protocol.GET_EEPROM.format(address, data_type)
            serial_id, response = self.send_and_receive(cmd)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return
            if response[0] == protocol.OK:
                if data_type == protocol.EEPROM_DATA_TYPE_FLOAT:
                    return float(response[1][1:])
                elif data_type == protocol.EEPROM_DATA_TYPE_INTEGER:
                    return int(response[1][1:])
                elif data_type == protocol.EEPROM_DATA_TYPE_BYTE:
                    return int(response[1][1:])
        except Exception as e:
            printf("Error {}".format(e))
            return None

# -------------------------------------------------------- Set Commands -----------------------------------------------#

    def set_position(self, x, y, z, speed=300, relative=False, wait=False):
        """
        Move uArm to the position (x,y,z) unit is mm, speed unit is mm/sec
        :param x:
        :param y:
        :param z:
        :param speed:
        :param relative
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        try:
            x = str(round(x, 2))
            y = str(round(y, 2))
            z = str(round(z, 2))
            s = str(round(speed, 2))
            if relative:
                command = protocol.SET_POSITION_RELATIVE.format(x, y, z, s)
            else:
                command = protocol.SET_POSITION.format(x, y, z, s)
            if wait:
                serial_id, response = self.send_and_receive(command)
                while self.get_is_moving():
                    time.sleep(0.05)
                if response is not None:
                    if response[0] == protocol.OK:
                        return True
                    else:
                        return False
            else:
                self.__send_msg(command)
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def set_pump(self, on, wait=False):
        """
        Control uArm Pump On or OFF
        :param on: True On, False OFF
        :param wait: if True, will block the thread, until get response or timeout
        :return: succeed True or Failed False
        """
        command = protocol.SET_PUMP.format(1 if on else 0)
        if wait:
            serial_id, response = self.send_and_receive(command)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                return True
            else:
                return False
        else:
            self.__send_msg(command)

    def set_gripper(self, catch, wait=False):
        """
        Turn On/Off Gripper
        :param catch: True On/ False Off
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        command = protocol.SET_GRIPPER.format(1 if catch else 0)
        if wait:
            serial_id, response = self.send_and_receive(command)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                return True
            else:
                return False
        else:
            self.__send_msg(command)

    def set_wrist(self, angle, wait=False):
        """
        Set uArm Hand Wrist Angle. Include servo offset.
        :param angle:
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        return self.set_servo_angle(protocol.SERVO_HAND, angle, wait=wait)

    def set_servo_angle(self, servo_number, angle, wait=False):
        """
        Set uArm Servo Angle, 0 - 180 degrees, this Function will include the manual servo offset.
        :param servo_number: lease reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
        :param angle: 0 - 180 degrees
        :param wait: if True, will block the thread, until get response or timeout
        :return: succeed True or Failed False
        """
        command = protocol.SET_SERVO_ANGLE.format(str(servo_number), str(angle))
        if wait:
            serial_id, response = self.send_and_receive(command)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                return True
            else:
                return False
        else:
            self.__send_msg(command)

    def set_buzzer(self, frequency, duration, wait=False):
        """
        Turn on the uArm Buzzer
        :param frequency: The frequency, in Hz
        :param duration: The duration of the buzz, in seconds
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        command = protocol.SET_BUZZER.format(frequency, duration)
        if wait:
            serial_id, response = self.send_and_receive(command)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                return True
            else:
                return False
        else:
            self.__send_msg(command)

    def set_servo_attach(self, servo_number=None, move=True, wait=False):
        """
        Set Servo status attach, Servo Attach will lock the servo, You can't move uArm with your hands.
        :param servo_number: If None, will attach all servos, please reference protocol.py SERVO_BOTTOM, SERVO_LEFT,
        SERVO_RIGHT, SERVO_HAND
        :param move: if True, will move to current position immediately
        :param wait: if True, will block the thread, until get response or timeout
        :return: succeed True or Failed False
        """
        if servo_number is not None:
            if move:
                pos = self.get_position()
                self.set_position(pos[0], pos[1], pos[2], speed=100)
            command = protocol.ATTACH_SERVO.format(servo_number)
            if wait:
                serial_id, response = self.send_and_receive(command)
                if response is None:
                    printf("No Message response {}".format(serial_id))
                    return None
                if response[0].startswith(protocol.OK):
                    return True
                else:
                    return False
            else:
                self.__send_msg(command)
        else:
            if move:
                pos = self.get_position()
                self.set_position(pos[0], pos[1], pos[2], speed=0)
            if wait:
                if self.set_servo_attach(servo_number=0, move=False, wait=True) \
                        and self.set_servo_attach(servo_number=1, move=False, wait=True) \
                        and self.set_servo_attach(servo_number=2, move=False, wait=True) \
                        and self.set_servo_attach(servo_number=3, move=False, wait=True):
                    return True
                else:
                    return False
            else:
                self.set_servo_attach(servo_number=0, move=False)
                self.set_servo_attach(servo_number=1, move=False)
                self.set_servo_attach(servo_number=2, move=False)
                self.set_servo_attach(servo_number=3, move=False)

    def set_servo_detach(self, servo_number=None, wait=False):
        """
        Set Servo status detach, Servo Detach will unlock the servo, You can move uArm with your hands.
        But move function won't be effect until you attach.
        :param servo_number: If None, will detach all servos, please reference protocol.py SERVO_BOTTOM, SERVO_LEFT,
         SERVO_RIGHT, SERVO_HAND
        :param wait: if True, will block the thread, until get response or timeout
        :return: succeed True or Failed False
        """
        if servo_number is not None:
            command = protocol.DETACH_SERVO.format(servo_number)
            if wait:
                serial_id, response = self.send_and_receive(command)
                if response is None:
                    printf("No Message response {}".format(serial_id))
                    return None
                if response[0].startswith(protocol.OK):
                    return True
                else:
                    return False
            else:
                self.__send_msg(command)
        else:
            if wait:
                if self.set_servo_detach(servo_number=0, wait=True) \
                        and self.set_servo_detach(servo_number=1, wait=True) \
                        and self.set_servo_detach(servo_number=2, wait=True) \
                        and self.set_servo_detach(servo_number=3, wait=True):
                    return True
                else:
                    return False
            else:
                self.set_servo_detach(servo_number=0)
                self.set_servo_detach(servo_number=1)
                self.set_servo_detach(servo_number=2)
                self.set_servo_detach(servo_number=3)

    def set_polar_coordinate(self, rotation, stretch, height, speed=100, wait=False):
        """
        Polar Coordinate, rotation, stretch, height.
        :param rotation:
        :param stretch:
        :param height:
        :param speed:
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        rotation = str(round(rotation, 2))
        stretch = str(round(stretch, 2))
        height = str(round(height, 2))
        speed = str(round(speed, 2))
        command = protocol.SET_POLAR.format(stretch, rotation, height, speed)
        if wait:
            self.__send_msg(command)
            while self.get_is_moving():
                time.sleep(0.05)
        # if wait:
        #     serial_id, response = self.send_and_receive(command)
        #     if response is None:
        #         printf("No Message response {}".format(serial_id))
        #         return None
        #     if response[0].startswith(protocol.OK):
        #         return True
        #     else:
        #         return False
        else:
            self.__send_msg(command)

# ---------------------------------------------------- Report Commands -----------------------------------------------#

    def set_report_button(self, wait=False):
        """
        Report Button pressed, this function will temporary disable system built-in
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        command = protocol.SET_REPORT_BUTTON.format(0)
        if wait:
            serial_id, response = self.send_and_receive(command)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                return True
            else:
                return False
        else:
            self.__send_msg(command)

    def close_report_button(self, wait=False):
        """
        Close report Button pressed event
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        command = protocol.SET_REPORT_BUTTON.format(1)
        if wait:
            serial_id, response = self.send_and_receive(command)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                return True
            else:
                return False
        else:
            self.__send_msg(command)

    def get_report_button(self, button, wait=False):
        """
        If call `set_report_button`, uArm will report button event once buttons have been press.
        store the position in LIFO queue.
        :param button , B0 - BUTTON_MENU, B1 - BUTTON_PLAY
        :param wait: if True, will block the thread, until get response or timeout
        :return: position array [x,y,z,r]
        """
        try:
            item = None
            if button == protocol.BUTTON_MENU:
                if wait:
                    item = self.__menu_button_queue.get(self.timeout)
                else:
                    item = self.__menu_button_queue.get(block=False)
                self.__menu_button_queue.task_done()
            elif button == protocol.BUTTON_PLAY:
                if wait:
                    item = self.__play_button_queue.get(self.timeout)
                else:
                    item = self.__play_button_queue.get(block=False)
                self.__play_button_queue.task_done()
            return item
        except Empty:
            return None

    def set_report_position(self, interval, wait=False):
        """
        Report Current Position in (interval) seconds.
        :param interval: Seconds if 0 disable report
        :param wait: if True, will block the thread, until get response or timeout
        :return
        """
        interval = str(round(interval, 2))
        command = protocol.SET_REPORT_POSITION.format(interval)
        if wait:
            serial_id, response = self.send_and_receive(command)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return None
            if response[0] == protocol.OK:
                return True
            else:
                return False
        else:
            self.__send_msg(command)

    def close_report_position(self, wait=False):
        """
        Stop Reporting the position
        :return:
        """
        self.set_report_position(0, wait=wait)

    def get_report_position(self):
        """
        If call `set_report_position`, uArm will report current position during the interval.
        Store the position in LIFO queue.
        :return: position array [x,y,z,r]
        """
        item = self.__position_queue.get(self.timeout)
        self.__position_queue.task_done()
        return item


if __name__ == '__main__':
    uarm = UArm()
    uarm.connect()
    printf(uarm.firmware_version())
    uarm.set_position(10, 150, 250, speed=100)
    uarm.set_position(10, 100, 250, speed=100)
    uarm.set_position(10, 200, 250, speed=100)
    uarm.set_position(10, 150, 200, speed=100)
    uarm.set_position(10, 150, 150, speed=100)
    uarm.set_position(10, 150, 100, speed=100)
    uarm.set_position(0, 150, 150, speed=100, wait=True)
    uarm.set_position(0, 150, 50, speed=100, wait=True)
    uarm.set_pump(True)
    uarm.set_position(0, 100, 0, speed=100, relative=True, wait=True)
    uarm.set_position(0, 0, 100, speed=100, relative=True, wait=True)
    uarm.set_buzzer(1000, 0.1)
    uarm.set_position(0, -100, 0, speed=100, relative=True, wait=True)
    uarm.set_position(0, 0, -100, speed=100, relative=True, wait=True)
    uarm.set_pump(False)
    uarm.set_position(-100, 0, 0, speed=100, relative=True, wait=True)
    uarm.set_position(100, 0, 0, speed=100, relative=True, wait=True)
    # uarm.set_polar_coordinate(133,26)
    # threading.Thread(target=lambda :uarm.set_servo_attach()).start()
    # threading.Thread(target=lambda :uarm.set_servo_attach()).start()
    uarm.set_position(0, 0, 100, relative=True, speed=100, wait=True)
    uarm.set_position(0, 100, 0, relative=True, speed=100, wait=True)
    uarm.set_position(0, 0, -100, relative=True, speed=100, wait=True)
