from __future__ import print_function
from .util import *
from .tools.list_uarms import uarm_ports
import serial
from .version import is_a_version,is_supported_version
import logging
from . import protocol
import time
#
# logging.basicConfig(filename='logger.log', level=logging.INFO)
#
# logging.info("------------------------------------")


class UArm(object):

    firmware_version = None
    product_type = None

    def __init__(self, port=None, debug=False, log=None):
        """
        :param port: UArm Serial Port name, if no port provide, will try first port we detect
        :param debug: if True, will print out all debug message
        :param log: log function, if no log function provide, will use standard print.
        :raise UArmConnectException
        :raise UnSupportedFirmwareVersionException
        :raise UnknownFirmwareException

        UArm port is immediately opened on object creation, if no port provide, we will detect all connected uArm serial
        devices. please reference `pyuarm.tools.list_uarms`
        port is a device name: depending on operating system. eg. `/dev/ttyUSB0` on GNU/Linux or `COM3` on Windows.
        debug will display all debug messages, include All serial commands.
        log is a function reference, if you don't provide log function, we will display to stdout
        """
        self.debug = debug
        if not port:
            ports = uarm_ports()
            if len(ports) > 0:
                port = ports[0]
            else:
                raise NoUArmPortException("No uArm ports is found.")
        if log is not None:
            self.log = log
        else:
            self.log = print
        self.port = port
        self.sp = serial.Serial(baudrate=115200,timeout=5)
        self.connect()

    def disconnect(self):
        """
        disconnect will release/close the uarm port
        :return:
        """
        self.log("Disconnect from port - {0}...".format(self.port))
        self.sp.close()

    def connect(self):
        try:
            self.sp.port = self.port
            self.log("Connecting from port - {0}...".format(self.port))
            self.sp.open()
            time.sleep(3)
        except serial.SerialException as e:
            raise UArmConnectException("Unable to connect to the port: {}, error: {}".format(self.port, e.strerror))
        self.responseLog = []
        try:
            # if self.is_ready():
            self.read_firmware_version()
        # print (self.read_firmware_version())
            if is_a_version(self.firmware_version):
                self.log("Firmware Version: {0}".format(self.firmware_version))
                if not is_supported_version(self.firmware_version):
                    raise UnSupportedFirmwareVersionException("Error: unsupported uArm Firmware version")
            else:
                raise UnknownFirmwareException("Error: unknown Firmware Version")
        except TypeError:
            raise UnknownFirmwareException("Error: unknown Firmware Version")

    def reconnect(self):
        """
        reconnect will open the uarm port
        :return:
        """
        self.connect()

    def is_connected(self):
        """
        is_connected will return the uarm connected status
        :return: connected status
        """
        if not self.sp.isOpen():
            return False
        else:
            return True

    # def is_ready(self):
    #     if self.send_cmd("gMov") == "F":
    #         self.log("connected...")
    #         return True
    #     else:
    #         return False

    def send_cmd(self, cmnd):
        # This command will send a command and recieve the robots response. There must always be a response!
        if not self.is_connected():
            return None

        # Prepare and send the command to the robot
        cmndString = "[" + cmnd + "]"
        if self.debug:
            self.log ("Send Command: {0}".format(cmndString))
        try:
            self.sp.flushInput()
            self.sp.write(cmndString)
        except serial.serialutil.SerialException as e:
            self.log("UArm.send_cmd(): ERROR {0} while sending command {1}. Disconnecting Serial!".format(e,cmnd))
            self.isConnected = False
            return False

        # Read the response from the robot (THERE MUST ALWAYS BE A RESPONSE!)
        try:
            response = self.sp.readline().strip()

        except serial.serialutil.SerialException as e:
            self.log("UArm.send_cmd(): ERROR {0}while sending command {1}. Disconnecting Serial!".format(e, cmnd))
            self.isConnected = False
            return False
        # Save the response to a log variable, in case it's needed for debugging
        self.responseLog.append((cmnd, response))

        # # Make sure the response has the valid start and end characters
        if not (response.count('[') == 1 and response.count(']') == 1):
            self.log("send_cmd(): ERROR: The message {0} did not come with proper formatting!".format(response))

        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")
        response = response.lower()

        # If the robot returned an error, print that out
        if response.startswith("f"):
            self.log("send_cmd(): ERROR: Received error from robot: {0}".format(response))

        if self.debug:
            self.log("response: {0}".format(response))
        return response

    def __parse_cmd(self, message, arguments):
        response_dict = {n: 0 for n in arguments}  # Fill the dictionary with zero's

        # Do error checking, in case communication didn't work
        if message is False:
            self.log("UArm.__parse_cmd(): Since an error occurred in communication, returning 0's for all arguments!")
            return response_dict

        # if command not in message:
        #     self.log("UArm.__parse_cmd(): ERROR: The message did not come with the appropriate command!")
        #     return response_dict
        #
        # # Get rid of the "command" part of the message, so it's just arguments and their numbers
        # message = message.replace(command, "")

        # Get the arguments and place them into the array
        for i, arg in enumerate(arguments):
            if i < len(arguments) - 1:
                response_dict[arg] = message[message.find(arg) + 1: message.find(arguments[i + 1])]
            else:
                response_dict[arg] = message[message.find(arg) + 1:]

            response_dict[arg] = float(response_dict[arg])

        return response_dict

# -------------------------------------------------------- Commands ----------------------------------------------------

    def read_firmware_version(self):
        """
        read the firmware version.
        Protocol Cmd: `protocol.GET_VERSION`
        :return: firmware version, if failed return False
        """
        cmd = protocol.GET_VERSION
        response = self.send_cmd(cmd)
        logging.info(response)
        if response.startswith("s"):
            values = response.split('-')
            self.product_type = values[0]
            self.firmware_version = values[1]
        else:
            return False

    def get_simulation(self, x, y, z):
        """
        validate the coordinate (x,y,z) if it can be reached or not.
        :param x:
        :param y:
        :param z:
        :return:
        """
        x = str(round(x, 2))
        y = str(round(y, 2))
        z = str(round(z, 2))
        cmd = protocol.SIMULATION.format(x,y,z)
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            return True
        else:
            return False

    def move_to(self, x, y, z, speed=300):
        x = str(round(x, 2))
        y = str(round(y, 2))
        z = str(round(z, 2))
        s = str(round(speed, 2))
        command = protocol.SET_MOVE.format(x,y,z,s)
        response = self.send_cmd(command)
        logging.info("response from move to: {}".format(response))
        if response.startswith("s"):
            return True
        elif response.startswith("f"):
            logging.info("move_to: failed in ({}, {}, {})".format(x,y,z))
            return False

    def set_servo_angle(self, servo_number, angle):
        cmd = protocol.SET_ANGLE.format(str(servo_number), str(angle))
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            return True
        else:
            return False

    def set_raw_angle(self, servo_number, angle):
        cmd = protocol.SET_RAW_ANGLE.format(str(servo_number), str(angle))
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            return True
        else:
            return False

    def move_wrist(self, angle):
        angle = str(round(angle, 3))
        cmd = "handV{0}".format(angle)
        if self.send_cmd(cmd) == "ok":
            return True
        else:
            return False

    def pump_on(self):
        if self.send_cmd(protocol.SET_PUMP.format(1)).startswith("s"):
            return True
        else:
            return False

    def pump_off(self):
        if self.send_cmd(protocol.SET_PUMP.format(0)).startswith("s"):
            return True
        else:
            return False

    def servo_attach(self, servo_number=None):
        if servo_number is not None:
            cmd = protocol.ATTACH_SERVO.format(servo_number)
            if self.send_cmd(cmd).startswith("s"):
                return True
            else:
                return False
        else:
            self.servo_attach(0)
            self.servo_attach(1)
            self.servo_attach(2)
            self.servo_attach(3)
            return True

    def servo_detach(self, servo_number=None):
        if servo_number is not None:
            cmd = protocol.DETACH_SERVO.format(servo_number)
            if self.send_cmd(cmd).startswith("s"):
                return True
            else:
                return False
        else:
            self.servo_detach(0)
            self.servo_detach(1)
            self.servo_detach(2)
            self.servo_detach(3)
            return True

    def set_buzzer(self, frequency, duration, stop_duration):
        cmd = protocol.SET_BUZZER.format(frequency,duration, stop_duration)
        if self.send_cmd(cmd).startswith("s"):
            return True
        else:
            return False

    def get_coordinate(self):
        # Returns an array of the format [x, y, z] of the robots current location

        response = self.send_cmd(protocol.GET_COOR)
        if response.startswith("s"):
            parse_cmd = self.__parse_cmd(response[1:], ["x", "y", "z"])
            coordinate = [parse_cmd["x"], parse_cmd["y"], parse_cmd["z"]]
            return coordinate
        else:
            return False

    def is_moving(self):
        # Returns a 0 or a 1, depending on whether or not the robot is moving.

        response = self.send_cmd(protocol.GET_IS_MOVE)
        if response == "f":
            return False
        elif response == "s":
            return True

    def gripper_catch(self):
        response = self.send_cmd(protocol.SET_GRIPPER.format(1))
        if response == "f":
            return False
        elif response == "s":
            return True

    def set_polar(self, rotation, stretch, height, speed=100):
        cmd = protocol.SET_POLAR.format(stretch, rotation, height, speed)
        if self.send_cmd(cmd).startswith("s"):
            return True
        else:
            return False

    def get_polar(self):
        cmd = protocol.GET_POLAR
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            parse_cmd = self.__parse_cmd(response[1:], ["s", "r", "h"])
            polar_crd = [parse_cmd["s"], parse_cmd["r"], parse_cmd["h"]]
            return polar_crd
        else:
            return False

    def get_servo_angle(self, servo_number=None):
        # Returns an angle in degrees, of the servo
        cmd = protocol.GET_ANGLE

        response = self.send_cmd(cmd)
        if response.startswith("s"):
            parse_cmd = self.__parse_cmd(response[1:],  ["b", "l", "r", "h"])
            angles = [parse_cmd["b"], parse_cmd["l"], parse_cmd["r"], parse_cmd["h"]]
            if servo_number is not None:
                if 0 <= servo_number <= 3:
                    return angles[servo_number]
                else:
                    return False
            else:
                return angles
        else:
            return False

    def get_raw_angle(self, servo_number=None):
        # Returns an angle in degrees, of the servo
        cmd = protocol.GET_RAW_ANGLE

        response = self.send_cmd(cmd)
        if response.startswith("s"):
            parse_cmd = self.__parse_cmd(response[1:],  ["b", "l", "r", "h"])
            angles = [parse_cmd["b"], parse_cmd["l"], parse_cmd["r"], parse_cmd["h"]]
            if servo_number is not None:
                if 0 <= servo_number <= 3:
                    return angles[servo_number]
                else:
                    return False
            else:
                return angles
        else:
            return False


    def get_tip_sensor(self):
        response = self.send_cmd(protocol.GET_TIP)
        if response == "f":
            return False
        elif response == "s":
            return True

    def get_eeprom(self, address, data_type=EEPROM_DATA_TYPE_BYTE):
        cmd = protocol.GET_EEPROM.format(address, data_type)
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            val = response[1:]
            if data_type == EEPROM_DATA_TYPE_FLOAT:
                return float(val)
            elif data_type == EEPROM_DATA_TYPE_INTEGER:
                return int(float(val))
            elif data_type == EEPROM_DATA_TYPE_BYTE:
                return int(float(val))

    def set_eeprom(self, address, data, data_type=EEPROM_DATA_TYPE_BYTE):
        cmd = protocol.SET_EEPROM.format(address, data_type, data)
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            return True

    def get_serial_number(self):
        serial_number = ""
        for i in range(15):
            serial_number += chr(int(self.get_eeprom(SERIAL_NUMBER_ADDRESS + i)))
        return serial_number

    def get_analog(self,pin):
        cmd = protocol.GET_ANALOG.format(pin)
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            val = response[1:]
            return int(float(val))

    def get_digital(self,pin):
        cmd = protocol.GET_DIGITAL.format(pin)
        response = self.send_cmd(cmd)
        if response.startswith("s"):
            val = response[1:]
            return val
