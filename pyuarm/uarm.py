from __future__ import print_function
import serial
from . import protocol
from .log import DEBUG, INFO, ERROR, printf, init_logger, set_default_logger, close_logger
from . import PY3
import time
import threading
from .tools.list_uarms import uarm_ports, get_port_property

if PY3:
    from queue import Queue, LifoQueue, Empty
else:
    from Queue import Queue, LifoQueue, Empty

# ################################### Exception ################################


def catch_exception(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            printf("{} - {} - {}".format(type(e).__name__, func.__name__, e), ERROR)
    return decorator


class UArmConnectException(Exception):
    def __init__(self, errno, message=None):
        """
        uArm Connect Exception
        :param errno: 0 Unable to connect uArm, 1 unknown firmware version, 2 unsupported uArm Firmware version
        :param message:
        """
        if message is None:
            self.message = ""
        else:
            self.message = message
        self.errno = errno
        if self.errno == 0:
            self.error = "Unable to connect uArm"
        elif self.errno == 1:
            self.error = "Unknown Firmware Version"
        elif self.errno == 2:
            self.error = "Unsupported uArm Firmware Version"
        elif self.errno == 3:
            self.error = "No available uArm Port"
        elif self.errno == 4:
            self.error = "uArm is not connected"
        else:
            self.error = "Not Defined Error"

    def __str__(self):
        return repr(self.error + "-" + self.message)


class UArm(object):
    def __init__(self, port_name=None, timeout=2, debug=False, logger=None):
        """
        :param port_name: UArm Serial Port name, if no port provide, will try first port we detect
        :param logger: if no logger provide, will create a logger by default
        :param debug: if Debug is True, create a Debug Logger by default
        :param timeout: default timeout is 5 sec.
        :raise UArmConnectException

        | if no port provide, we will detect all connected uArm serial devices.
        | please reference `pyuarm.tools.list_uarms`
        | port is a device name: depending on operating system.
        | eg. `/dev/ttyUSB0` on GNU/Linux or `COM3` on Windows.
        | logger will display all info/debug/error/warning messages.
        """
        self.__init_property()
        self.timeout = timeout
        if port_name is not None:
            self.port_name = port_name
        if logger is None:
            set_default_logger(debug)
        else:
            init_logger(logger)

    def __init_property(self):
        self.timeout = None
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
        self.__connect_flag = False

    def __init_serial_core(self):
        if PY3:
            from .threaded import UArmSerial, UArmReaderThread
            self.__reader_thread = UArmReaderThread(self.__serial, UArmSerial, self.__data_buf)
            self.__reader_thread.start()
            self.__reader_thread.connect()
            self.__transport, self.__protocol = self.__reader_thread.connect()
        else:
            self.__connect_flag = True

    def __close_serial_core(self):
        if PY3:
            self.__reader_thread.stop()
        else:
            self.__connect_flag = False

    @catch_exception
    def connect(self):
        """
        This function will open the port immediately. Function will wait for the READY Message for 5 secs.
        | Once received READY message, will finish connection.
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
            if self.connection_state:
                break
        self.__receive_thread.start()
        self.__send_thread.start()
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.__isReady:
                break

    @property
    def connection_state(self):
        """
        Return the uArm Connection status.
        :return: boolean
        """
        if PY3:
            if self.__protocol is not None:
                return self.__protocol.get_connect_status()
            else:
                return False
        else:
            if self.__serial is not None:
                return self.__serial.is_open and self.__connect_flag
            else:
                return False

    @catch_exception
    def disconnect(self):
        """
        Disconnect the serial connection, terminate all queue and thread
        """
        self.__close_serial_core()
        self.__serial.close()
        printf("Disconnect from {}".format(self.port_name))

    @catch_exception
    def close(self):
        """
        Release all resources:
            | - logger
            | - queue
            | - thread
        """
        if self.connection_state:
            self.disconnect()
        close_logger()
        self.__init_property()

    def __process_line(self, line):
        if line is not None:
            if line.startswith("$"):
                values = line.split(' ')
                msg_id = int(values[0].replace('$', ''))
                self.msg_buff[msg_id] = values[1:]
                printf("MSG Received: {}".format(line), DEBUG)
            elif line.startswith(protocol.READY):
                printf("Received MSG: {}".format(line), DEBUG)
                self.__isReady = True
            elif line.startswith(protocol.REPORT_POSITION_PREFIX):
                printf("POSITION REPORT: {}".format(line), DEBUG)
                values = line.split(' ')
                pos_array = [float(values[1][1:]), float(values[2][1:]),
                             float(values[3][1:])]
                self.__position_queue.put(pos_array, block=False)

    def __receive_thread_process(self):
        """
        This Function is for receiving thread. Under Python3.x we will use `pyserial threading`_ to manage
        the send/receive logic.
        | This thread will be finished if serial connection is end.
        .. _pyserial threading: http://pyserial.readthedocs.io/en/latest/pyserial_api.html#module-serial.threaded
        """
        while self.connection_state:
            try:
                line = None
                if PY3:
                    if len(self.__data_buf) > 0:
                        line = self.__data_buf.pop().rstrip('\r\n')
                else:
                    line = self.__serial.readline().rstrip('\r\n')
                    if not line:
                        continue
                self.__process_line(line)
            except serial.SerialException as e:
                printf("Receive Process Fatal - {}".format(e), ERROR)
                if not PY3:
                    self.__connect_flag = False
            except Exception as e:
                printf("Receive Process {} - {}".format(type(e).__name__, e), ERROR)
            time.sleep(0.001)
        # Make Sure all queues were release
        self.__position_queue.join()
        self.__play_button_queue.join()
        self.__menu_button_queue.join()

    def __send_thread_process(self):
        """
        This function is for sending thread function.
        | All functions which start with ``get_`` and with ``wait=True`` function will send out with this thread.
        | thread will be finished if serial connection is end.
        """
        while self.connection_state:
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
                printf("Send {}".format(msg), DEBUG)
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
        Generate a serial id to identify the message.
        :return: Integer serial id
        """
        if self.serial_id == 65535:  # Maximum id
            self.serial_id = 1
        else:
            self.serial_id += 1
        return self.serial_id

    def send_and_receive(self, msg):
        """
        This function will block until receive the response message.
        :param msg: String Serial Command
        :return: (Integer msg_id, String response) and None if no response
        """
        if self.connection_state:
            msg_id = self.__gen_serial_id()
            item = {'id': msg_id, 'msg': msg}
            self.__send_queue.put(item)
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if msg_id in self.msg_buff.keys():
                    return msg_id, self.msg_buff[msg_id]
            # print("duration: {}".format(time.time() - start_time))
            return None, None
        else:
            raise UArmConnectException(4)

    def send_msg(self, msg):
        """
        This function will send out the message and return the serial_id immediately.
        :param msg: String, Serial Command
        :return:
        """
        if self.connection_state:
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
            raise UArmConnectException(4)

# -------------------------------------------------------- Commands ---------------------------------------------------#

    def reset(self):
        """
        Reset include below action:
        - Attach all servos
        - Move to default position (0, 150, 150) with speed 100mm/min
        - Turn off Pump/Gripper
        - Set Wrist Servo to Angle 90
        :return:
        """
        self.set_servo_attach()
        time.sleep(0.1)
        self.set_position(0, 150, 150, speed=100, wait=True)
        self.set_pump(False)
        self.set_gripper(False)
        self.set_wrist(90)

# -------------------------------------------------------- Get Commands -----------------------------------------------#
    @property
    @catch_exception
    def firmware_version(self):
        """
        Get the firmware version.
        Protocol Cmd: ``protocol.GET_FIRMWARE_VERSION``
        :return: firmware version, if failed return None
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
    @catch_exception
    def hardware_version(self):
        """
        Get the Product version.
        Protocol Cmd: `protocol.GET_HARDWARE_VERSION``
        :return: firmware version, if failed return None
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

    @catch_exception
    def get_position(self):
        """
        Get Current uArm position (x,y,z)
        :return: Float Array. Returns an array of the format [x, y, z] of the robots current location
        """
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

    @catch_exception
    def get_is_moving(self):
        """
        Get the uArm current moving status.
        :return: Boolean True or False
        """
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

    @catch_exception
    def get_polar(self):
        """
        get Polar coordinate
        :return: Float Array. Return an array of the format [rotation, stretch, height]
        """
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

    @catch_exception
    def get_tip_sensor(self):
        """
        Get Status from Tip Sensor
        :return: True On/ False Off
        """
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

    @catch_exception
    def get_servo_angle(self, servo_num=None):
        """
        Get Servo Angle
        :param servo_num: if servo_num not provide, will return a array. for all servos, servo 0
        , servo 1, servo 2, servo 3
        :return:
        """
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

    @catch_exception
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

    @catch_exception
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

    @catch_exception
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

    @catch_exception
    def set_position(self, x=None, y=None, z=None, speed=300, relative=False, wait=False):
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
        if relative:
            if x is None:
                x = 0.0
            if y is None:
                y = 0.0
            if z is None:
                z = 0.0
            x = str(round(x, 2))
            y = str(round(y, 2))
            z = str(round(z, 2))
            s = str(round(speed, 2))
            command = protocol.SET_POSITION_RELATIVE.format(x, y, z, s)
        else:
            if x is None or y is None or z is None:
                raise Exception('x, y, z can not be None in absolute mode')
            x = str(round(x, 2))
            y = str(round(y, 2))
            z = str(round(z, 2))
            s = str(round(speed, 2))
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
            self.send_msg(command)

    @catch_exception
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
            self.send_msg(command)

    @catch_exception
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
            self.send_msg(command)

    @catch_exception
    def set_wrist(self, angle, wait=False):
        """
        Set uArm Hand Wrist Angle. Include servo offset.
        :param angle:
        :param wait: if True, will block the thread, until get response or timeout
        :return:
        """
        return self.set_servo_angle(protocol.SERVO_HAND, angle, wait=wait)

    @catch_exception
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
            self.send_msg(command)

    @catch_exception
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
            self.send_msg(command)

    @catch_exception
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
                self.send_msg(command)
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

    @catch_exception
    def set_servo_detach(self, servo_number=None, wait=False):
        """
        Set Servo status detach, Servo Detach will unlock the servo, You can move uArm with your hands.
        But move function won't be effect until you attach.
        :param servo_number: If None, will detach all servos, please reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
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
                self.send_msg(command)
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

    @catch_exception
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
            self.send_msg(command)
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
            self.send_msg(command)

# ---------------------------------------------------- Report Commands -----------------------------------------------#

    @catch_exception
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
            self.send_msg(command)

    @catch_exception
    def close_report_position(self, wait=False):
        """
        Stop Reporting the position
        :return:
        """
        self.set_report_position(0, wait=wait)

    @catch_exception
    def get_report_position(self):
        """
        If call `set_report_position`, uArm will report current position during the interval.
        Store the position in LIFO queue.
        :return: position array [x,y,z,r]
        """
        item = self.__position_queue.get(self.timeout)
        self.__position_queue.task_done()
        return item

    def __del__(self):
        self.close()


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
