from __future__ import print_function
import serial
from . import version, protocol, util
from .util import *
from .tools.list_uarms import uarm_ports, get_port_property, check_port_plug_in
from . import PY3
import time
import threading
if PY3:
    from queue import Queue
else:
    from Queue import Queue

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
        return UArm(port_name=ports[0],logger=logger)
    else:
        printf("There is no uArm port available",ERROR)
        return None

class UArm(object):



    def __delete__(self, instance):
        self.close()
        printf("Deleted...")

    def __init__(self, port_name=None, logger=None, debug=False, block=True, timeout=0.1):
        """
        :param port_name: UArm Serial Port name, if no port provide, will try first port we detect
        :param logger: if no logger provide, will create a logger by default
        :param debug: if Debug is True, create a Debug Logger by default
        :param timeout: if no timeout, will be block mode
        :raise UArmConnectException

        UArm port is immediately opened on object creation, if no port provide, we will detect all connected uArm serial
        devices. please reference `pyuarm.tools.list_uarms`
        port is a device name: depending on operating system. eg. `/dev/ttyUSB0` on GNU/Linux or `COM3` on Windows.
        logger will display all info/debug/error/warning messages.
        """
        if logger is None:
            util.init_logger(util.get_default_logger(debug))
        else:
            util.init_logger(logger)
        if port_name is None:
            ports = uarm_ports()
            if len(ports) > 0:
                port_name = ports[0]
            else:
                raise UArmConnectException(0, "No uArm ports is found.")
        self.block = block
        self.timeout = timeout
        self.port = get_port_property(port_name)
        self.connect()

    def __send_thread_process(self):
        """
        this function is for sending thread function, All serial writable function should be through this thread,
        thread will be finished if serial connection is end.
        :return:
        """
        try:
            while not self.__stop_flag:
                item = self.__send_queue.get()
                if item is None:
                    break
                msg = item['msg']
                printf("Send MSG: {}".format(msg), DEBUG)
                if PY3:
                    b = bytes(msg, encoding='ascii')
                    self.__serial.write(b)
                else:
                    self.__serial.write(msg)
                id_item = {"id": item['id'], "wait": item['wait']}
                self.__send_queue_id.put(id_item,block=item['wait'])
                self.__send_queue.task_done()
        except Exception as e:
            printf("Send Process exception  {}".format(e))

        # print("Send Task End")

    def __receive_thread_process(self):
        """
        this Function is for receiving thread function, All serial response message would store in __receive_queue.
        This thread will be finished if serial connection is end.
        :return:
        """
        while not self.__stop_flag and self.__serial.is_open:
            try:
                line = self.__serial.readline()
                if not line:
                    continue
                if PY3:
                    line = str(line, encoding='ascii').rstrip()
                if line.startswith("$"):
                    printf("Received MSG: {}".format(line), DEBUG)
                    values = line.split(' ')
                    id = int(values[0].replace('$', ''))
                    id_item = self.__send_queue_id.get()
                    if id_item['wait']:
                        item = {"id": id, "params": values[1:]}
                        self.__receive_queue.put(item,block=self.block)
                    self.__send_queue_id.task_done()
                elif line.startswith(protocol.READY):
                    printf("Received MSG: {}".format(line), DEBUG)
                    self.__isReady = True
                elif line.startswith(protocol.REPORT_POSITION_PREFIX):
                    printf("POSITION REPORT: {}".format(line), DEBUG)
                    values = line.split(' ')
                    pos_array = [float(values[1][1:]), float(values[2][1:]), float(values[3][1:]), float(values[4][1:])]
                    self.__position_queue.put(pos_array,block=self.block)
            except serial.SerialException as e:
                printf("Receive Process Error {} - {}".format(e.errno, e))
                self.__isConnected = False
                break
            except TypeError as e:
                printf("Receive Process Error {}".format(e))
                break

    def disconnect(self):
        """
        Disconnect the serial connection, terminate all queue and thread
        :return:
        """
        self.__stop_flag = True
        self.__isConnected = False
        printf("Disconnect from port - {0}...".format(self.port.device))
        try:
            self.__serial.close()
        except OSError as e:
            printf("Error occured when try to close serial port: {}".format(e))
        self.__stop_flag = True
        self.__position_queue.join()
        self.__receive_queue.join()
        self.__send_queue.join()
        self.__send_queue_id.join()
        self.__position_queue.put(None)
        self.__receive_queue.put(None)
        self.__send_queue.put(None)
        self.__send_queue_id.put(None)
        self.__receive_thread.join()
        self.__send_thread.join()
        self.__serial = None

    def close(self):
        """
        Close function will release all resources, including serial port, logger, all threads
        :return:
        """
        util.close_logger()
        if self.__serial is not None:
            self.disconnect()


    def connect(self):
        """
        This function will open the port immediately. Function will wait for the READY Message for 5 secs. Once received
        READY message, Function will send the Version search command.
        :return:
        """
        self.firmware_version = None
        self.hardware_version = None
        self.__isConnected = False
        self.__isReady = False
        self.__stop_flag = False
        self.serial_id = 0
        self.__serial = serial.Serial(baudrate=115200, timeout=0.1)
        self.__receive_thread = threading.Thread(target=self.__send_thread_process)
        self.__send_thread = threading.Thread(target=self.__receive_thread_process)
        # self.__receive_thread.setDaemon(True)
        # self.__send_thread.setDaemon(True)
        self.__send_queue = Queue()
        self.__send_queue_id = Queue()
        self.__receive_queue = Queue()
        self.__position_queue = Queue()
        try:
            self.__serial.port = self.port.device
            printf("Connecting from port - {0}...".format(self.port.device))
            self.__serial.open()
            self.__receive_thread.start()
            self.__send_thread.start()
            if self.block:
                self.__connect()
            else:
                threading.Thread(target=self.__connect).start()
        except serial.SerialException as e:
            raise UArmConnectException(0, "port: {}, Error: {}".format(self.port.device, e.strerror))

    def __connect(self):
        start_time = time.time()
        while time.time() - start_time < 5:
            if self.__isReady:
                break
        printf("Connected...")
        if not self.__isReady:
            self.disconnect()
            raise UArmConnectException(1, "{} message received timeout.".format(protocol.READY))

        self.get_firmware_version()
        self.get_hardware_version()
        if version.is_a_version(self.firmware_version):
            printf("Firmware Version: {0}".format(self.firmware_version))
            if not version.is_supported_version(self.firmware_version):
                raise UArmConnectException(2,"Firmware Version: {}".format(self.firmware_version))
            else:
                self.__isConnected = True
        else:
            raise UArmConnectException(1, "Firmware Version: {}".format(self.firmware_version))

    def is_connected(self):
        """
        is_connected will return the uarm connected status
        :return: connected status
        """
        if self.__serial is not None:
            if self.__serial.isOpen() and self.__isConnected:
                return True
            else:
                return False
        else:
            return False

    def __push_request_item(self, cmd, wait):
        """
        Push the message to sending queue
        :param cmd:
        :param wait:
        :return:
        """
        serial_id = self.__gen_serial_id()
        msg = "#{} {}\n".format(serial_id, cmd)
        item = {"id":serial_id, "msg":msg, "wait":wait}
        self.__send_queue.put(block=self.block,item=item)
        return serial_id

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

    def __pop_response_item(self, serial_id):
        """
        Get response message from the __receive_queue
        :param serial_id:
        :return:
        """
        if self.__receive_queue.not_empty:
            item = self.__receive_queue.get(self.timeout)
            self.__receive_queue.task_done()
            if serial_id != item['id']:
                return None
            else:
                return item

# -------------------------------------------------------- Commands ---------------------------------------------------#

# -------------------------------------------------------- Get Commands -----------------------------------------------#
    def get_firmware_version(self):
        """
        Get the firmware version.
        Protocol Cmd: `protocol.GET_FIRMWARE_VERSION`
        :return: firmware version, if failed return False
        """
        try:
            cmd = protocol.GET_FIRMWARE_VERSION
            serial_id = self.__push_request_item(cmd,True)
            response = self.__pop_response_item(serial_id)
            self.firmware_version = response['params'][1].replace('V','')
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_hardware_version(self):
        """
        Get the Product version.
        Protocol Cmd: `protocol.GET_HARDWARE_VERSION`
        :return: firmware version, if failed return False
        """
        try:
            cmd = protocol.GET_HARDWARE_VERSION
            serial_id = self.__push_request_item(cmd, True)
            response = self.__pop_response_item(serial_id)
            self.hardware_version = response['params'][1].replace('V','')
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_tip_sensor(self):
        """
        Get Status from Tip Sensor
        :return: True On/ False Off
        """
        try:
            serial_id= self.__push_request_item(protocol.GET_TIP_SENSOR,wait=True)
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf ("No Message response {}".format(serial_id))
                return
            if response['params'][1] == 'V0':
                return True
            elif response['params'][1] == 'V1':
                return False
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
            serial_id= self.__push_request_item(protocol.GET_SERVO_ANGLE,wait=True)
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf ("No Message response {}".format(serial_id))
                return
            servo_0 = float(response['params'][1][1:])
            servo_1 = float(response['params'][2][1:])
            servo_2 = float(response['params'][3][1:])
            servo_3 = float(response['params'][4][1:])
            servo_array = [servo_0, servo_1, servo_2, servo_3]
            if servo_num == None:
                return servo_array
            elif servo_num == 0:
                return servo_0
            elif servo_num == 1:
                return servo_1
            elif servo_num == 2:
                return servo_2
            elif servo_num == 3:
                return servo_3
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_position(self):
        """
        Get Current uArm position (x,y,z) mm
        :return: Returns an array of the format [x, y, z] of the robots current location
        """
        try:
            serial_id= self.__push_request_item(protocol.GET_COOR,wait=True)
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf ("No Message response {}".format(serial_id))
                return
            x = float(response['params'][1][1:])
            y = float(response['params'][2][1:])
            z = float(response['params'][3][1:])
            coordinate = [x,y,z]
            return coordinate
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_polar(self):
        """
        get Polar coordinate
        :return: Return an array of the format [rotation, stretch, height]
        """
        try:
            serial_id= self.__push_request_item(protocol.GET_POLAR, wait=True)
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf ("No Message response {}".format(serial_id))
                return
            stretch     = float(response['params'][1][1:])
            rotation    = float(response['params'][2][1:])
            height      = float(response['params'][3][1:])
            polar = [rotation,stretch,height]
            return polar
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
            serial_id = self.__push_request_item(cmd, wait=self.block)
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf ("No Message response {}".format(serial_id))
                return
            val = "".join(response['params'][1:])[1:]
            if data_type == protocol.EEPROM_DATA_TYPE_FLOAT:
                return float(val)
            elif data_type == protocol.EEPROM_DATA_TYPE_INTEGER:
                return int(val)
            elif data_type == protocol.EEPROM_DATA_TYPE_BYTE:
                return int(val)
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_analog(self,pin):
        """
        Get Analog Value from specific PIN
        :param pin:
        :return:
        """
        try:
            cmd = protocol.GET_ANALOG.format(pin)
            serial_id = self.__push_request_item(cmd, wait=self.block)
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf ("No Message response {}".format(serial_id))
                return
            printf("DEBUG response: {}".format(response['params']))
            val = "".join(response['params'][1:])[1:]
            return int(float(val))
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def get_digital(self,pin):
        """
        Get Digital Value from specific PIN.
        :param pin:
        :return:
        """
        try:
            cmd = protocol.GET_DIGITAL.format(pin)
            serial_id= self.__push_request_item(cmd,wait=True)
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf ("No Message response {}".format(serial_id))
                return
            if response['params'][1] == 'V0':
                return 0
            elif response['params'][1] == 'V1':
                return 1
        except Exception as e:
            printf("Error {}".format(e))
            return None


    def is_moving(self):
        """
        Detect is uArm moving
        :return: Returns a 0 or a 1, depending on whether or not the robot is moving.
        """
        serial_id = self.__push_request_item(protocol.GET_IS_MOVE,True)
        response = self.__pop_response_item(serial_id)
        if response is None:
            printf ("No Message response {}".format(serial_id))
            # printf ("Serial MSG ID not correct:request - {}, response - {}".format(serial_id,response['id']))
            return
        # if serial_id != response['id']:
        #     return None
        try:
            if response['params'][1] == 'V1':
                return True
            elif response['params'][1] == 'V0':
                return False
        except Exception as e:
            printf("Error {}".format(e))



# -------------------------------------------------------- Set Commands -----------------------------------------------#
    def set_position(self, x, y, z, speed=300, relative=False, wait=False):
        """
        Move uArm to the position (x,y,z) unit is mm, speed unit is mm/sec
        :param x:
        :param y:
        :param z:
        :param speed:
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
            serial_id = self.__push_request_item(command, self.block)
            if wait:
                while self.is_moving():
                    time.sleep(0.05)
            if self.block:
                response = self.__pop_response_item(serial_id=serial_id)
                if response is None:
                    printf("No Message response {}".format(serial_id))
                    return
                if response['params'][0].startswith(protocol.OK):
                    return True
                else:
                    return False
        except Exception as e:
            printf("Error {}".format(e))
            return None

    def set_pump(self, ON):
        """
        Control uArm Pump On or OFF
        :param ON: True On, False OFF
        :return: succeed True or Failed False
        """
        self.__push_request_item(protocol.SET_PUMP.format(1 if ON else 0),False)

    def set_gripper(self, catch):
        """
        Turn On/Off Gripper
        :param catch: True On/ False Off
        :return:
        """
        self.__push_request_item(protocol.SET_GRIPPER.format(1 if catch else 0), False)

    def set_wrist(self, angle):
        """
        Set uArm Hand Wrist Angle. Include servo offset.
        :param angle:
        :return:
        """
        self.set_servo_angle(protocol.SERVO_HAND, angle)

    def set_servo_angle(self, servo_number, angle):
        """
        Set uArm Servo Angle, 0 - 180 degrees, this Function will include the manual servo offset.
        :param servo_number: lease reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
        :param angle: 0 - 180 degrees
        :return: succeed True or Failed False
        """
        self.serial_id = self.__push_request_item(protocol.SET_SERVO_ANGLE.format(str(servo_number), str(angle)), False)

    def set_buzzer(self, frequency, duration):
        """
        Turn on the uArm Buzzer
        :param frequency: The frequency, in Hz
        :param duration: The duration of the buzz, in seconds
        :return:
        """
        self.serial_id = self.__push_request_item(protocol.SET_BUZZER.format(frequency, duration), False)

    def set_polar_coordinate(self, rotation, stretch, height, speed=100,wait=False):
        """
        Polar Coordinate, rotation, stretch, height.
        :param rotation:
        :param stretch:
        :param height:
        :param speed:
        :return:
        """
        rotation = str(round(rotation, 2))
        stretch = str(round(stretch, 2))
        height = str(round(height, 2))
        speed = str(round(speed, 2))
        command = protocol.SET_POLAR.format(stretch, rotation, height, speed)
        serial_id = self.__push_request_item(command, wait)
        if wait:
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf("No Message response {}".format(serial_id))
                return
        # if wait:
        #     while self.is_moving():
        #         printf("Still Moving",type=DEBUG)
        if wait:
            if response['params'][0].startswith(protocol.OK):
                return True
            else:
                return False

    def set_servo_attach(self, servo_number=None, move=False):
        """
        Set Servo status attach, Servo Attach will lock the servo, You can't move uArm with your hands.
        :param servo_number: If None, will attach all servos, please reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
        :param move: if True, will move to current position immediately
        :return: succeed True or Failed False
        """
        if servo_number is not None:
            if move:
                pos = self.get_position()
                self.set_position(pos[0],pos[1],pos[2],speed=0)
            cmd = protocol.ATTACH_SERVO.format(servo_number)
            serial_id = self.__push_request_item(cmd, wait=self.block)
            if self.block:
                response = self.__pop_response_item(serial_id=serial_id)
                if response is None:
                    printf("No Message response {}".format(serial_id))
                    # printf ("Serial MSG ID not correct:request - {}, response - {}".format(serial_id,response['id']))
                    return
                if response['params'][0].startswith(protocol.OK):
                    return True
                else:
                    return False
        else:
            if move:
                pos = self.get_position()
                self.set_position(pos[0],pos[1],pos[2],speed=0)
            if self.block:
                if self.set_servo_attach(0) \
                        and self.set_servo_attach(1) \
                        and self.set_servo_attach(2) \
                        and self.set_servo_attach(3):
                    return True
                else:
                    return False
            else:
                self.set_servo_attach(0)
                self.set_servo_attach(1)
                self.set_servo_attach(2)
                self.set_servo_attach(3)

    def set_servo_detach(self, servo_number=None):
        """
        Set Servo status detach, Servo Detach will unlock the servo, You can move uArm with your hands. But move function won't be effect until you attach.
        :param servo_number: If None, will detach all servos, please reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
        :return: succeed True or Failed False
        """
        if servo_number is not None:
            cmd = protocol.DETACH_SERVO.format(servo_number)
            serial_id = self.__push_request_item(cmd, wait=self.block)
            if self.block:
                response = self.__pop_response_item(serial_id=serial_id)
                if response is None:
                    printf("No Message response {}".format(serial_id))
                    # printf ("Serial MSG ID not correct:request - {}, response - {}".format(serial_id,response['id']))
                    return
                if response['params'][0].startswith(protocol.OK):
                    return True
                else:
                    return False
        else:
            if self.block:
                if self.set_servo_detach(0) and self.set_servo_detach(1) \
                        and self.set_servo_detach(2) and self.set_servo_detach(3):
                    return True
                else:
                    return False
            else:
                self.set_servo_detach(0)
                self.set_servo_detach(1)
                self.set_servo_detach(2)
                self.set_servo_detach(3)

    def set_rom_data(self, address, data, data_type=protocol.EEPROM_DATA_TYPE_BYTE):
        """
        Set DATA to EEPROM
        :param address: 0 - 2048
        :param data: Value
        :param data_type: EEPROM_DATA_TYPE_FLOAT, EEPROM_DATA_TYPE_INTEGER, EEPROM_DATA_TYPE_BYTE
        :return:
        """
        cmd = protocol.SET_EEPROM.format(address, data_type, data)
        serial_id = self.__push_request_item(cmd, wait=self.block)
        if self.block:
            response = self.__pop_response_item(serial_id=serial_id)
            if response is None:
                printf("No Message response {}".format(serial_id))
                # printf ("Serial MSG ID not correct:request - {}, response - {}".format(serial_id,response['id']))
                return
            if response['params'][0].startswith(protocol.OK):
                return True
            else:
                return False

# ---------------------------------------------------- Report Commands -----------------------------------------------#

    def set_report_position(self, interval):
        """
        Report Current Position in (interval) seconds.
        :param interval: Seconds if 0 disable report
        """
        interval = str(round(interval, 2))
        self.__push_request_item(protocol.SET_REPORT_POSITION.format(interval),False)

    def close_report_position(self):
        """
        Stop Reporting the position
        :return:
        """
        self.set_report_position(0)

    def get_report_position(self):
        """
        If call `set_report_position`, uArm will report current position during the interval.
        pyuarm will store the position in FIFO queue.
        :return: position array [x,y,z,r]
        """
        item = self.__position_queue.get(self.timeout)
        self.__position_queue.task_done()
        return item
