from __future__ import print_function
from util import NoUArmPortException,UnknownFirmwareException, UnSupportedFirmwareVersionException
from tools.list_uarms import uarm_ports
import serial
import time
from version import is_a_version,is_supported_version


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
            self.sp = serial.Serial(port=port,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                bytesize=serial.EIGHTBITS,
                                timeout=.1)
        except serial.SerialException as e:
            self.log("UArm connect to the port: {}, error: {}".format(port,e.message))
        time.sleep(3)
        self.responseLog = []
        try:
            self.firmware_version = self.read_firmware_version()
            if is_a_version(self.firmware_version):
                self.log("Firmware Version: {0}".format(self.firmware_version))
                if not is_supported_version(self.firmware_version):
                    raise UnSupportedFirmwareVersionException("Error: unsupported uArm Firmware version")
            else:
                raise UnknownFirmwareException("Error: unknown Firmware Version")
        except TypeError:
            raise UnknownFirmwareException("Error: unknown Firmware Version")

    def is_connected(self):
        if not self.sp.isOpen():
            return False
        else:
            return True

    def send_cmd(self, cmnd):
        # This command will send a command and recieve the robots response. There must always be a response!
        if not self.is_connected():
            return None

        # Prepare and send the command to the robot
        cmndString = bytes("[" + cmnd + "]>", encoding='ascii')
        try:
            self.sp.write(cmndString)
        except serial.serialutil.SerialException as e:
            self.log("UArm.send_cmd(): ERROR {0} while sending command {1}. Disconnecting Serial!".format(e,cmnd))
            self.isConnected = False
            return False

        # Read the response from the robot (THERE MUST ALWAYS BE A RESPONSE!)
        response = ""
        while True:

            try:
                response += str(self.sp.read(), 'ascii')
            except serial.serialutil.SerialException as e:
                self.log("UArm.send_cmd(): ERROR {0}while sending command {1}. Disconnecting Serial!".format(e, cmnd))
                self.isConnected = False
                return False

            if "\n" in response:
                response = response[:-1]
                break

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
            self.log("Uarm.read(): ERROR: Recieved error from robot: {0}".format(response))

        if self.debug:
            print("response: {0}".format(response))
        return response

    def read_cmd(self, message, command, arguments):
        response_dict = {n: 0 for n in arguments}  # Fill the dictionary with zero's

        # Do error checking, in case communication didn't work
        if message is False:
            self.log("Uarm.__parseArgs(): Since an error occured in communication, returning 0's for all arguments!")
            return response_dict

        if command not in message:
            self.log("Uarm.__parseArgs(): ERROR: The message did not come with the appropriate command!")
            return response_dict

        # Get rid of the "command" part of the message, so it's just arguments and their numbers
        message = message.replace(command, "")

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
        cmd = "gVer"
        return self.send_cmd(cmd)

    def move_to(self, x, y, z, speed=5):
        x = str(round(x, 2))
        y = str(round(y, 2))
        z = str(round(z, 2))
        s = str(round(speed, 2))
        command = "moveX{0}Y{1}Z{2}S{3}".format(x,y,z,s)
        return self.send_cmd(command)

    def move_wrist(self, angle):
        angle = str(round(angle, 3))
        cmd = "handV{0}".format(angle)
        return self.send_cmd(cmd)

    def pump_on(self):
        return self.send_cmd("pumpV1")

    def pump_off(self):
        return self.send_cmd("pumpV0")

    def servo_attach(self, servo_number):
        servo_number = str(int(servo_number))
        cmd = "attachS{}".format(servo_number)
        return self.send_cmd(cmd)

    def servo_detach(self, servo_number):
        servo_number = str(int(servo_number))
        cmnd = "detachS" + servo_number
        return self.send_cmd(cmnd)

    def set_buzzer(self, frequency, duration):
        cmnd = "buzzF" + str(frequency) + "T" + str(duration)
        return self.send_cmd(cmnd)

    def get_coordinate(self):
        # Returns an array of the format [x, y, z] of the robots current location

        response = self.send_cmd("gcoords")

        parse_cmd = self.read_cmd(response, "coords", ["x", "y", "z"])
        coordinate = [parse_cmd["x"], parse_cmd["y"], parse_cmd["z"]]

        return coordinate

    def get_is_moving(self):
        # Returns a 0 or a 1, depending on whether or not the robot is moving.

        response = self.send_cmd("gmoving")

        parse_cmd = self.read_cmd(response, "moving", ["m"])
        return parse_cmd["m"]

    def get_servo_angle(self, servo_number):
        # Returns an angle in degrees, of the servo

        cmnd = "gAngleS" + str(servo_number)
        response = self.send_cmd(cmnd)
        parse_cmd = self.read_cmd(response, "angle", ["a"])

        return parse_cmd["a"]

    def get_tip_sensor(self):
        # Returns 0 or 1, whether or not the tip sensor is currently activated

        response  = self.send_cmd("gtip")
        parse_cmd = self.read_cmd(response, "tip", ["v"])

        return (True, False)[int(parse_cmd['v'])]  # Flip the value and turn it into a boolean
