from __future__ import print_function
import serial
from . import version, protocol, util
from .util import printf, ERROR, DEBUG, UArmConnectException, get_default_logger
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

    firmware_version = None
    hardware_version = None
    __isConnected = False
    __receive_thread = None
    __send_thread = None
    __send_queue = Queue()
    __send_queue_id = Queue()
    # __send_message_type = {}
    __receive_queue = Queue()
    __stop_flag = False
    serial_id = -1

    def __init__(self, port_name=None, logger=None, debug=False, block=True):
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
        self.__receive_thread = threading.Thread(target=self.__send_thread_process)
        self.__send_thread = threading.Thread(target=self.__receive_thread_process)
        self.__receive_thread.setDaemon(True)
        self.__send_thread.setDaemon(True)


        self.port = get_port_property(port_name)
        self.__serial = serial.Serial(baudrate=115200, timeout=0.1)
        self.connect()

    def __send_thread_process(self):
        """
        this function is for __send thread running
        :return:
        """
        while not self.__stop_flag:
            # if self.__send_queue.not_empty:
                item = self.__send_queue.get()
                self.__send_queue.task_done()
                msg = item['msg']
                printf("Send MSG: {}".format(msg, DEBUG))
                if PY3:
                    b = bytes(msg,encoding='ascii')
                    self.__serial.write(b)
                else:
                    self.__serial.write(msg)
                id_item = {"id": item['id'], "wait": item['wait']}
                self.__send_queue_id.put(id_item)

                # time.sleep(0.03) # This is the best delay for current uArm IOT chip (UNO)

    def __receive_thread_process(self):
        while not self.__stop_flag:
            line = self.__serial.readline()
            # printf("line: {}".format(line))
            if not line:
                continue
            if PY3:
                line = str(line, encoding='ascii').rstrip()
            if line.startswith("$"):
                printf("Received MSG: {}".format(line), DEBUG)
                values = line.split(' ')
                id = int(values[0].replace('$',''))
                id_item = self.__send_queue_id.get()
                if id_item['wait']:
                    item = {"id":id, "params":values[1:]}
                    self.__receive_queue.put(item)
            elif line.startswith(protocol.READY):
                printf("Received MSG: {}".format(line), DEBUG)
                self.__isConnected = True

    def disconnect(self):
        """
        disconnect will release/close the uarm port
        :return:
        """
        printf("Disconnect from port - {0}...".format(self.port.device))
        self.__serial.close()
        self.__isConnected = False
        self.checking_port_flag = False
        self.__stop_flag = True

    def connect(self):
        """
        This function will open the port immediately. Function will wait for the READY Message for 5 secs. Once received
        READY message, Function will send the Version search command.
        :return:
        """
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
        # item = self.__receive_queue.get(block=True,timeout=5)
        start_time = time.time()
        while time.time() - start_time < 5:
            if self.__isConnected:
                break
        printf("Connected...")
        if not self.__isConnected:
                raise UArmConnectException(1, "{} message received timeout.".format(protocol.READY))

        self.get_firmware_version()
        self.get_hardware_version()
        if version.is_a_version(self.firmware_version):
            printf("Firmware Version: {0}".format(self.firmware_version))
            if not version.is_supported_version(self.firmware_version):
                raise UArmConnectException(2,"Firmware Version: {}".format(self.firmware_version))
        else:
            raise UArmConnectException(1, "Firmware Version: {}".format(self.firmware_version))

    def is_connected(self):
        """
        is_connected will return the uarm connected status
        :return: connected status
        """
        # try:
        #     if PY3:
        #         self.__gen_serial_id()
        #         cmnd = "#{} {}".format(self.serial_id, protocol.GET_FIRMWARE_VERSION)
        #         cmndString = bytes(cmnd + "\n", encoding='ascii')
        #         self.__serial.write(cmndString)
        #         response = str(self.__serial.readline(),encoding='ascii')
        #     else:
        #         self.__gen_serial_id()
        #         cmnd = "#{} {}".format(self.serial_id, protocol.GET_FIRMWARE_VERSION)
        #         cmndString = bytes(cmnd + "\n")
        #         self.__serial.write(cmndString)
        #         response = self.__serial.readline()
        # except serial.serialutil.SerialException:
        #     self.__isConnected = False
        if self.__serial.isOpen() and self.__isConnected:
            return True
        else:
            return False


    def __push_request_item(self, cmd, wait):
        serial_id = self.__gen_serial_id()
        msg = "#{} {}\n".format(serial_id, cmd)
        item = {"id":serial_id, "msg":msg, "wait":wait}
        # printf("push msg: {}".format(msg))
        self.__send_queue.put(block=self.block,item=item)

        # self.__send_message_type['id'] = wait
        return serial_id

    def __gen_serial_id(self):
        if self.serial_id == 65535:
            self.serial_id = 0
        else:
            self.serial_id += 1
        return self.serial_id

    def __pop_response_item(self, serial_id):
        if self.__receive_queue.not_empty:
            item = self.__receive_queue.get()
            self.__receive_queue.task_done()
            # print ("item id: {}, serial_id: {}".format(item['id'],serial_id))
            if serial_id != item['id']:
                return self.__pop_response_item(serial_id)
            else:
                return item


    def __gen_response_value(self, response):
        if response.startswith(protocol.OK.lower()):
            return response.rstrip().split(' ')[1:]
        else:
            return False


    # def __send_and_receive(self, cmnd, timeout=None):
    #     """
    #     This command will send a command and receive the uArm response. There must always be a response!
    #     Responses should be recieved immediately after sending the command, after which the robot will proceed to
    #     perform the action.
    #     :param cmnd: a String command, to send to the robot
    #     :return: The robots response
    #     """
    #
    #     if not self.is_connected():
    #         printf("Communication| Tried to send a command while robot was not connected!")
    #         return ""
    #
    #     # Prepare and send the command to the robot
    #     self.__gen_serial_id()
    #     cmnd = "#{} {}".format(self.serial_id,cmnd)
    #     printf("Coummunication | Send Message: {}, total length: {}".format(cmnd,len(cmnd)), type=DEBUG)
    #     if PY3:
    #         cmndString = bytes(cmnd + "\n", encoding='ascii')
    #     else:
    #         cmndString = bytes(cmnd + "\n")
    #
    #     try:
    #         self.__serial.write(cmndString)
    #
    #     except serial.serialutil.SerialException as e:
    #         # printf("while sending command {}. Disconnecting Serial! \nError: {}".format(cmndString, str(e)),type=ERROR)
    #         self.__isConnected = False
    #         return ""
    #
    #     try:
    #         if PY3:
    #             response = str(self.__serial.readline(),encoding='ascii')
    #         else:
    #             response = self.__serial.readline()
    #         if response.startswith("${}".format(self.serial_id)):
    #             if "E20" in response or "E21" in response:
    #                 printf("Communication| ERROR: send {}, received error from robot: {}".format(cmndString, response), type=ERROR)
    #                 return ""
    #             response = response.replace('\n', '')
    #             response = response.replace('${} '.format(self.serial_id),'')
    #             printf("Communication| [{}] {}{}".format(cmnd, " " * (30 - len(cmnd)), response), type=DEBUG)
    #         else:
    #             printf("Communication| ERROR: send {}, received error from robot: {}".format(cmndString, response), type=ERROR)
    #             # printf("Communication| ERROR: received error from robot: {}".format(response),type=ERROR)
    #             return ""
    #         return response.lower()
    #     except serial.serialutil.SerialException as e:
    #         printf("while sending command {}. Disconnecting Serial! \nError: {}".format(cmnd,str(e)), type=ERROR)
    #         self.__isConnected = False
    #         return ""

    # def __parse_cmd(self, message, arguments):
    #     response_dict = {n: 0 for n in arguments}  # Fill the dictionary with zero's
    #
    #     # Do error checking, in case communication didn't work
    #     if message is False:
    #         printf("UArm.__parse_cmd(): Since an error occurred in communication, returning 0's for all arguments!")
    #         return response_dict
    #
    #     # if command not in message:
    #     #     printf("UArm.__parse_cmd(): ERROR: The message did not come with the appropriate command!")
    #     #     return response_dict
    #     #
    #     # # Get rid of the "command" part of the message, so it's just arguments and their numbers
    #     # message = message.replace(command, "")
    #
    #     # Get the arguments and place them into the array
    #     for i, arg in enumerate(arguments):
    #         if i < len(arguments) - 1:
    #             response_dict[arg] = message[message.find(arg) + 1: message.find(arguments[i + 1])]
    #         else:
    #             response_dict[arg] = message[message.find(arg) + 1:]
    #
    #         response_dict[arg] = float(response_dict[arg])
    #
    #     return response_dict

# -------------------------------------------------------- Commands ----------------------------------------------------

    def get_firmware_version(self):
        """
        Get the firmware version.
        Protocol Cmd: `protocol.GET_FIRMWARE_VERSION`
        :return: firmware version, if failed return False
        """
        cmd = protocol.GET_FIRMWARE_VERSION
        serial_id = self.__push_request_item(cmd,True)
        response = self.__pop_response_item(serial_id)
        # if serial_id != response['id']:
        #     printf ("Serial MSG ID not correct:request - {}, response - {}".format(serial_id,response['id']))
        #     return
        self.firmware_version = response['params'][1].replace('V','')


    def get_hardware_version(self):
        """
        Get the Product version.
        Protocol Cmd: `protocol.GET_HARDWARE_VERSION`
        :return: firmware version, if failed return False
        """
        cmd = protocol.GET_HARDWARE_VERSION
        serial_id = self.__push_request_item(cmd, True)
        response = self.__pop_response_item(serial_id)
        # if serial_id != response['id']:
        #     printf ("Serial MSG ID not correct:request - {}, response - {}".format(serial_id,response['id']))
        #     return
        self.hardware_version = response['params'][1].replace('V','')

    # def get_simulation(self, x, y, z):
    #     """
    #     validate the coordinate (x,y,z) if it can be reached or not.
    #     :param x:
    #     :param y:
    #     :param z:
    #     :return:
    #     """
    #     x = str(round(x, 2))
    #     y = str(round(y, 2))
    #     z = str(round(z, 2))
    #     cmd = protocol.SIMULATION.format(x, y, z)
    #     response = self.__send_and_receive(cmd)
    #     value = self.__gen_response_value(response)
    #     if value:
    #         return value
    #     else:
    #         return False

    def set_position(self, x, y, z, speed=300, relative=False, wait=False):
        """
        Move uArm to the position (x,y,z) unit is mm, speed unit is mm/sec
        :param x:
        :param y:
        :param z:
        :param speed:
        :return:
        """
        x = str(round(x, 2))
        y = str(round(y, 2))
        z = str(round(z, 2))
        s = str(round(speed, 2))
        if relative:
            command = protocol.SET_POSITION_RELATIVE.format(x, y, z, s)
        else:
            command = protocol.SET_POSITION.format(x, y, z, s)
        self.__push_request_item(command, False)
        # response = self.__send_and_receive(command)
            # response = self.__pop_response_item()
            # if serial_id != response['id']:
            #     printf("Serial MSG ID not correct:request - {}, response - {}".format(serial_id, response['id']))
        if wait:
            while self.is_moving():
                printf("Still Moving",type=DEBUG)
                    # time.sleep(0.05)
            # if response['params'][0].startswith(protocol.OK.lower()):
            #     return True
            # else:
            #     return False
        # else:
        #     pass
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

    def set_pump(self, ON):
        """
        Control uArm Pump On or OFF
        :param ON: True On, False OFF
        :return: succeed True or Failed False
        """
        self.__push_request_item(protocol.SET_PUMP.format(1 if ON else 0),False)
        # cmd = protocol.SET_PUMP.
        # response = self.__send_and_receive(cmd)
        # if response.startswith(protocol.OK.lower()):
        #     return True
        # else:
        #     return False


    # def set_servo_angle(self, servo_number, angle):
    #     """
    #     Set uArm Servo Angle, 0 - 180 degrees, this Function will include the manual servo offset.
    #     :param servo_number: lease reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
    #     :param angle: 0 - 180 degrees
    #     :return: succeed True or Failed False
    #     """
    #     cmd = protocol.SET_ANGLE.format(str(servo_number), str(angle))
    #     response = self.__send_and_receive(cmd)
    #     if response.startswith(protocol.OK.lower()):
    #         return True
    #     else:
    #         return False
    #
    #
    # def set_wrist(self, angle):
    #     """
    #     Set uArm Hand Wrist Angle. Include servo offset.
    #     :param angle:
    #     :return:
    #     """
    #     return self.set_servo_angle(protocol.SERVO_HAND, angle)
    #

    #
    # def set_servo_attach(self, servo_number=None):
    #     """
    #     Set Servo status attach, Servo Attach will lock the servo, You can't move uArm with your hands.
    #     :param servo_number: If None, will attach all servos, please reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
    #     :return: succeed True or Failed False
    #     """
    #     if servo_number is not None:
    #         cmd = protocol.ATTACH_SERVO.format(servo_number)
    #         response = self.__send_and_receive(cmd)
    #         if response.startswith(protocol.OK.lower()):
    #             return True
    #         else:
    #             return False
    #     else:
    #         if self.set_servo_attach(0) and self.set_servo_attach(1) \
    #                 and self.set_servo_attach(2) and self.set_servo_attach(3):
    #             return True
    #         else:
    #             return False
    #
    # def set_servo_detach(self, servo_number=None):
    #     """
    #     Set Servo status detach, Servo Detach will unlock the servo, You can move uArm with your hands. But move function won't be effect until you attach.
    #     :param servo_number: If None, will detach all servos, please reference protocol.py SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
    #     :return: succeed True or Failed False
    #     """
    #     if servo_number is not None:
    #         cmd = protocol.DETACH_SERVO.format(servo_number)
    #         response = self.__send_and_receive(cmd)
    #         if response.startswith(protocol.OK.lower()):
    #             return True
    #         else:
    #             return False
    #     else:
    #         if self.set_servo_detach(0) and self.set_servo_detach(1) \
    #                 and self.set_servo_detach(2) and self.set_servo_detach(3):
    #             return True
    #         else:
    #             return False
    #
    # def set_buzzer(self, frequency, duration):
    #     """
    #     Turn on the uArm Buzzer
    #     :param frequency: The frequency, in Hz
    #     :param duration: The duration of the buzz, in seconds
    #     :return:
    #     """
    #     cmd = protocol.SET_BUZZER.format(frequency, duration)
    #     response = self.__send_and_receive(cmd)
    #     if response.startswith(protocol.OK.lower()):
    #         return True
    #     else:
    #         return False
    #
    # def get_position(self):
    #     """
    #     Get Current uArm position (x,y,z) mm
    #     :return: Returns an array of the format [x, y, z] of the robots current location
    #     """
    #     response = self.__send_and_receive(protocol.GET_COOR)
    #     value = self.__gen_response_value(response)
    #     if value:
    #         parse_cmd = self.__parse_cmd(response, ["x", "y", "z"])
    #         coordinate = [parse_cmd["x"], parse_cmd["y"], parse_cmd["z"]]
    #         return coordinate
    #     else:
    #         return False
    #

        # response = self.__send_and_receive(protocol.GET_IS_MOVE)
        # value = self.__gen_response_value(response)
        # if value:
        #     printf("".join(value[1:]))
            # if "".join(value)[1:] == "1":
            #     return True
            # else:
            #     return False
        # else:
        #     return False
    #
    # def set_gripper(self, catch):
    #     """
    #     Turn On/Off Gripper
    #     :param catch: True On/ False Off
    #     :return:
    #     """
    #     cmd = protocol.SET_GRIPPER.format(1 if catch else 0)
    #     response = self.__send_and_receive(cmd)
    #     if response.startswith(protocol.OK.lower()):
    #         return True
    #     else:
    #         return False
    #
    # # def set_polar_coordinate(self, rotation, stretch, height, speed=100):
    # #     """
    # #     Polar Coordinate, rotation, stretch, height.
    # #     :param rotation:
    # #     :param stretch:
    # #     :param height:
    # #     :param speed:
    # #     :return:
    # #     """
    # #     cmd = protocol.SET_POLAR.format(stretch, rotation, height, speed)
    # #     if self.__send_and_receive(cmd).startswith("s"):
    # #         return True
    # #     else:
    # #         return False
    # #
    # # def get_polar_coordinate(self):
    # #     cmd = protocol.GET_POLAR
    # #     response = self.__send_and_receive(cmd)
    # #     if response.startswith("s"):
    # #         parse_cmd = self.__parse_cmd(response[1:], ["s", "r", "h"])
    # #         polar_crd = [parse_cmd["s"], parse_cmd["r"], parse_cmd["h"]]
    # #         return polar_crd
    # #     else:
    # #         return False
    #
    # def get_servo_angle(self, servo_number=None):
    #     """
    #     Get Current uArm Servo Angles include offset
    #     :param servo_number: if None, Return 4 servos Current Angles
    #     :return: Returns an angle in degrees, of the servo
    #     """
    #     cmd = protocol.GET_ANGLE
    #
    #     response = self.__send_and_receive(cmd)
    #
    #     value = self.__gen_response_value(response)
    #     if value:
    #         parse_cmd = self.__parse_cmd(response, ["b", "l", "r", "h"])
    #         angles = [parse_cmd["b"], parse_cmd["l"], parse_cmd["r"], parse_cmd["h"]]
    #         if servo_number is not None:
    #             if 0 <= servo_number <= 3:
    #                 return angles[servo_number]
    #             else:
    #                 return False
    #         else:
    #             return angles
    #     else:
    #         return False
    #
    #
    # def get_tip_sensor(self):
    #     """
    #     Get Status from Tip Sensor
    #     :return: True On/ False Off
    #     """
    #     response = self.__send_and_receive(protocol.GET_TIP_SENSOR)
    #     value = self.__gen_response_value(response)
    #
    #     if value:
    #         if "".join(value)[1:] == "0":
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False
    #
    # def get_rom_data(self, address, data_type=protocol.EEPROM_DATA_TYPE_BYTE):
    #     """
    #     Get DATA From EEPROM
    #     :param address: 0 - 2048
    #     :param data_type: EEPROM_DATA_TYPE_FLOAT, EEPROM_DATA_TYPE_INTEGER, EEPROM_DATA_TYPE_BYTE
    #     :return:
    #     """
    #     cmd = protocol.GET_EEPROM.format(address, data_type)
    #     response = self.__send_and_receive(cmd)
    #     value = self.__gen_response_value(response)
    #     if value:
    #         # print("val: {}".format(type)))
    #         val = "".join(value)[1:]
    #
    #         if data_type == protocol.EEPROM_DATA_TYPE_FLOAT:
    #             return float(val)
    #         elif data_type == protocol.EEPROM_DATA_TYPE_INTEGER:
    #             return int(val)
    #         elif data_type == protocol.EEPROM_DATA_TYPE_BYTE:
    #             return int(val)
    #     else:
    #         return False
    #
    #
    # def set_rom_data(self, address, data, data_type=protocol.EEPROM_DATA_TYPE_BYTE):
    #     """
    #     Set DATA to EEPROM
    #     :param address: 0 - 2048
    #     :param data: Value
    #     :param data_type: EEPROM_DATA_TYPE_FLOAT, EEPROM_DATA_TYPE_INTEGER, EEPROM_DATA_TYPE_BYTE
    #     :return:
    #     """
    #     cmd = protocol.SET_EEPROM.format(address, data_type, data)
    #     response = self.__send_and_receive(cmd)
    #     if response.startswith(protocol.OK.lower()):
    #         return True
    #     else:
    #         return False
    #
    # def get_sn_number(self):
    #     """
    #     Get Serial Number
    #     :return:
    #     """
    #     serial_number = ""
    #     for i in range(15):
    #         serial_number += chr(int(self.get_rom_data(protocol.SERIAL_NUMBER_ADDRESS + i)))
    #     return serial_number
    #
    # def get_analog(self,pin):
    #     cmd = protocol.GET_ANALOG.format(pin)
    #     response = self.__send_and_receive(cmd)
    #     if response.startswith("s"):
    #         val = response[1:]
    #         return int(float(val))
    #
    # def get_digital(self,pin):
    #     cmd = protocol.GET_DIGITAL.format(pin)
    #     response = self.__send_and_receive(cmd)
    #     if response.startswith("s"):
    #         val = response[1:]
    #         return val
