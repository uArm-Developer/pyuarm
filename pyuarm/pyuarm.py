from __future__ import print_function
from util import NoUArmPortException,UnknownFirmwareException, UnSupportedFirmwareVersionException, UArmConnectException, get_uarm
from tools.list_uarms import uarm_ports
import serial
from version import is_a_version,is_supported_version
import logging
import protocol
import time

logging.basicConfig(filename='logger.log', level=logging.INFO)

logging.info("------------------------------------")


class UArm(object):

    def __init__(self, port=None, debug=False, log=None):
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
        self.debug = debug
        self.log("Initialize uArm, port is {0}...".format(port))
        try:
            self.sp = serial.Serial(port=port,baudrate=115200)
            time.sleep(3)
        except serial.SerialException as e:
            raise UArmConnectException("Unable to connect to the port: {}, error: {}".format(port, e.strerror))
        self.responseLog = []
        try:
            # if self.is_ready():
            self.firmware_version = self.read_firmware_version()
        # print (self.read_firmware_version())
            if is_a_version(self.firmware_version):
                self.log("Firmware Version: {0}".format(self.firmware_version))
                if not is_supported_version(self.firmware_version):
                    raise UnSupportedFirmwareVersionException("Error: unsupported uArm Firmware version")
            else:
                raise UnknownFirmwareException("Error: unknown Firmware Version")
        except TypeError:
            raise UnknownFirmwareException("Error: unknown Firmware Version")

    def disconnect(self):
        self.sp.close()

    def reconnect(self):
        self.sp.open()

    def is_connected(self):
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

        # Make sure the response has the valid start and end characters
        if not (response.count('[') == 1 and response.count(']') == 1):
            self.log("Uarm.read(): ERROR: The message {0} did not come with proper formatting!".format(response))

        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")
        response = response.lower()

        # If the robot returned an error, print that out
        if "ERROR" in response:
            self.log("Uarm.read(): ERROR: Received error from robot: {0}".format(response))

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
        cmd = protocol.GET_VERSION
        response = self.send_cmd(cmd)
        logging.info(response)
        if response.startswith("s"):
            return response[1:]
        else:
            return False

    def validate_coordinate(self, x, y, z):
        x = str(round(x, 2))
        y = str(round(y, 2))
        z = str(round(z, 2))
        cmd = protocol.SIMULATION.format(x,y,z)
        response = self.send_cmd(cmd)
        print (response)

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

    def write_servo_angle(self,servo_number,angle):
        cmd = protocol.SET_SERVO_ANGLE.format(str(servo_number),str(angle))
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

    def servo_attach(self, servo_number):
        cmd = protocol.ATTACH_SERVO.format(servo_number)
        if self.send_cmd(cmd).startswith("s"):
            return True
        else:
            return False

    def servo_detach(self, servo_number):
        cmd = protocol.DETACH_SERVO.format(servo_number)
        if self.send_cmd(cmd).startswith("s"):
            return True
        else:
            return False

    def set_buzzer(self, frequency, duration):
        cmd = protocol.SET_BUZZER.format(frequency,duration)
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

    def get_servo_angle(self, servo_number=None):
        # Returns an angle in degrees, of the servo
        cmd = protocol.GET_SERVO_ANGLE

        response = self.send_cmd(cmd)
        if response.startswith("s"):
            parse_cmd = self.__parse_cmd(response[1:],  ["t", "l", "r"])
            angles = [parse_cmd["r"], parse_cmd["l"], parse_cmd["r"]]
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