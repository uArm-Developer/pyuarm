#!/usr/bin/env python
#
# This is a module that help user to control your uArm.
# Please use -h to list all parameters of this script

# This file is part of pyuarm. https://github.com/uArm-Developer/pyuarm
# (C) 2016 UFACTORY <developer@ufactory.cc>


import pyuarm
from cmd import Cmd
from pyuarm.tools.list_uarms import get_uarm_port_cli ,uarm_ports
from pyuarm.tools import firmware_helper
import subprocess
from colorama import Fore, Back, init, Style

# logging.basicConfig(filename='logger.log', level=logging.INFO)
#
# logging.info("------------------------------------")
#

# class bcolors:
#     HEADER = '\033[95m'
#     OKBLUE = '\033[94m'
#     OKGREEN = '\033[92m'
#     WARNING = '\033[93m'
#     FAIL = '\033[91m'
#     ENDC = '\033[0m'
#     BOLD = '\033[1m'
#     UNDERLINE = '\033[4m'

init()


class UArmCmd(Cmd):

    help_msg = Style.BRIGHT + Fore.MAGENTA + "Shortcut:" + Fore.RESET + Style.RESET_ALL + "\n"
    help_msg += "Quit: " + Style.BRIGHT + Fore.RED + "Ctrl + D" + Fore.RESET + Style.RESET_ALL
    help_msg += ", or input: " + Back.BLACK + Fore.WHITE + "quit" + Fore.RESET + Style.RESET_ALL + "\n"
    help_msg += "Clear Screen: " + Style.BRIGHT + Fore.RED + "Ctrl + L" + Fore.RESET + Style.RESET_ALL

    ON_OFF = ['on', 'off']

    FIRMWARE =['version', 'force', 'upgrade']

    SERVO_STATUS = ['attach', 'detach']

    prompt = ">>> "
    intro = "Welcome to use {}uArm Command Line{}\n"\
        .format(Fore.YELLOW, Fore.RESET)

    intro += help_msg
    intro += "\n\n"
    intro += "Input {}{}help{}{} for more usage".format(Back.BLACK, Fore.WHITE,Fore.RESET, Back.RESET)

    # doc_header = "documented commands:"
    ruler = '-'

    uarm = None

    def __init__(self,  *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)

    def __is_connected(self):
        if self.uarm is None:
            print ("No uArm is connected, please use {}{}connect{}{}".format(Back.BLACK, Fore.WHITE,Fore.RESET, Back.RESET))
            return False
        else:
            if self.uarm.is_connected():
                return True
            else:
                print ("No uArm is connected, please use {}{}connect{}{}".format(Back.BLACK, Fore.WHITE,Fore.RESET, Back.RESET))
                return False

    def do_connect(self, arg):
        """
        connect, Open uArm Port, if more than one uArm Port found, will prompt options to choose.
        Please connect to uArm before you do any control action
        """
        if self.uarm is None:
            ports = uarm_ports()
            if len(ports) > 1:
                uarm_port = get_uarm_port_cli()
                try:
                    self.uarm = pyuarm.uArm(uarm_port)
                except pyuarm.UnknownFirmwareException:
                    print ("Unknown Firmware, please use {}{}uarm-firmware -upgrade{}{} to your firmware"
                           .format(Back.BLACK, Fore.WHITE,Fore.RESET, Back.RESET))
            elif len(ports) == 1:
                self.uarm = pyuarm.uArm()
            elif len(ports) == 0:
                print ("No uArm ports is found.")
        else:
            if self.uarm.is_connected():
                print ("uArm is already connected, port: {}".format(self.uarm.port))
            else:
                if self.uarm.reconnect():
                    print ("uArm port: {} is reconnected")

    def do_disconnect(self,arg):
        """
        disconnect, Release uarm port.
        """
        if self.uarm is not None:
            if self.uarm.is_connected():
                self.uarm.disconnect()

    def do_move_to(self, arg):
        """
        move_to, move to destination coordinate.
        format: move_to X Y Z or move_to X Y Z S
        X,Y,Z unit millimeter, S means Speed, unit mm/s
        eg. move_to 100 200 150
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 3:
                result = self.uarm.move_to(int(values[0]), int(values[1]), int(values[2]))
                msg = "succeed" if result else "failed"
                print (msg)
            elif len(values) == 4:
                result = self.uarm.move_to(int(values[0]), int(values[1]), int(values[2]), int(values[3]))
                msg = "succeed" if result else "failed"
                print (msg)

    def do_mv(self, args):
        """
        same with move_to
        """
        self.do_move_to(args)

    def do_get_coord(self, arg):
        """
        get_coord get current coordinate
        """
        if self.__is_connected():
            coords = self.uarm.read_coordinate()
            print ("Current coordinate: X-{} Y-{} Z-{}".format(coords.pop(),coords.pop(),coords.pop()))

    def do_pump(self, arg):
        """
        pump
        turn on/off pump
        """
        if self.__is_connected():
            if arg == 'on':
                result = self.uarm.pump_control(True)
                print ("succeed" if result else "failed")
            elif arg == 'off':
                result = self.uarm.pump_control(False)
                print ("succeed" if result else "failed")
            elif arg == '':
                print ("please input argument: {}".format(','.join(self.ON_OFF)))
            else:
                print ("Command not found {}".format(arg))

    def complete_pump(self, text, line, begidx, endidx):
        if not text:
            completions = self.ON_OFF[:]
        else:
            completions = [f
                           for f in self.ON_OFF
                           if f.startswith(text)
                           ]
        return completions

    # def do_sim(self, arg):
    #     """
    #     sim
    #     format: sim X Y Z
    #     validate the coordinate.
    #     eg. sim 100 200 100
    #     succeed
    #     """
    #     if self.__is_connected():
    #         values = arg.split(' ')
    #         if len(values) == 3:
    #             result = self.uarm.get_simulation(int(values[0]), int(values[1]), int(values[2]))
    #             msg = "succeed" if result else "failed"
    #             print (msg)

    def do_write_angle(self, arg):
        """
        write_angle
        format: write_angle servo_number angle
        servo_number:
            0 bottom servo,
            1 left servo,
            2 right servo,
            3 hand servo
        eg.
        >>> write_angle 0 90
        succeed
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                servo_num = int(values[0])
                angle = float(values[1])
                result = self.uarm.write_servo_angle(servo_num, angle)
                msg = "succeed" if result else "failed"
                print (msg)

    def do_read_angle(self, arg):
        """
        read_angle
        Read current servo angle.
        format: read_angle servo_number
        servo_number:
            0 bottom servo,
            1 left servo,
            2 right servo,
        if no servo_number provide, will list all servos angle
        eg.
        >>> read_angle
        Current Servo Angles: b-35.25, l-53.4, r-35.25
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 1:
                if values[0] == '':
                    angles = self.uarm.read_servo_angle()
                    print ("Current Servo Angles: b-{}, l-{}, r-{}".format(angles.pop(),angles.pop(),angles.pop()))

                else:
                    servo_num = int(values[0])
                    angle = self.uarm.read_servo_angle(servo_num)
                    print (angle)

    def do_alarm(self, arg):
        """
        alarm
        control buzzer
        format: alarm frequency duration
        eg.
        alarm 1 1
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                start = int(values[1])
                frequency = int(values[0])
                duration = start
                result = self.uarm.alarm(frequency,start,duration)
                msg = "succeed" if result else "failed"
                print (msg)

    def do_set_polar(self, arg):
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                result = self.uarm.write_stretch(values[0], values[1])
                msg = "succeed" if result else "failed"
                print (msg)
            # if len(values) == 3:
            #     result = self.uarm.write_stretch(values[0], values[1], values[2])
            #     msg = "succeed" if result else "failed"
            #     print (msg)

    # def do_get_polar(self, arg):
    #     if self.__is_connected():
    #         result = self.uarm.get_polar()
    #         if result:
    #             print ("polar coordinate: {}".format(result))

    def do_debug(self, arg):
        is_debug = False
        if arg.lower() == 'on':
            is_debug = True
        elif arg.lower() == 'off':
            is_debug = False

        if self.uarm:
            self.uarm.debug = is_debug

    def do_servo(self, arg):
        """
        Servo status
        format: servo attach servo_number
                servo detach servo_number
        servo_number:
            0 bottom servo,
            1 left servo,
            2 right servo,
            3 hand servo
            all
        eg. servo attach all
            servo detach all
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                if values[0] == 'attach':
                    if values[1] == 'all':
                        self.uarm.attach_all_servos()
                    elif values[1].isdigit():
                        v = int(values[1])
                        if 0 <= v <= 3:
                            self.uarm.set_servo_status(v,True)
                elif values[0] == 'detach':
                    if values[1] == 'all':
                        self.uarm.detach_all_servos()
                    elif values[1].isdigit():
                        v = int(values[1])
                        if 0 <= v <= 3:
                            self.uarm.set_servo_status(v,False)

    def complete_servo(self, text, line, begidx, endidx):
        if not text:
            completions = self.SERVO_STATUS[:]
        else:
            completions = [f
                           for f in self.SERVO_STATUS
                           if f.startswith(text)
                           ]
        return completions

    # def do_serial(self, arg):
    #     """
    #     Raw Serial Mode
    #     You could direct input the communication protocol here.
    #     """
    #     if self.__is_connected():
    #         serial_mode = SerialMode(self.uarm)
    #         serial_mode.cmdloop()

    def do_firmware(self, arg):
        """
        Firmware command
        sub command: version, upgrade, force
        version - display Remote Firmware version and local Firmware version (if connected)
        upgrade - if remote version latter than local firmware version, will flash the latest firmware to uarm
        force - force upgrade

        """
        if arg == 'version':
            print ("Remote Firmware Version: {}".format(firmware_helper.get_latest_version()))
            if self.__is_connected():
                print ("Local Firmware Version: {}".format(self.uarm.firmware_version))
        elif arg == 'upgrade':
            if self.uarm is not None:
                if self.uarm.is_connected():
                    self.uarm.disconnect()
                subprocess.call(['uarm-firmware','-u', '-p', self.uarm.port])
            else:
                subprocess.call(['uarm-firmware','-u'])
        elif arg == 'force':
            if self.uarm is not None:
                if self.uarm.is_connected():
                    self.uarm.disconnect()
                subprocess.call(['uarm-firmware','-d', '-f', '-p', self.uarm.port])
            else:
                subprocess.call(['uarm-firmware','-df'])
        elif arg == '':
            print ("please input argument: {}".format(','.join(self.FIRMWARE)))
        else:
            print ("command not found: {}".format(arg))

    def complete_firmware(self, text, line, begidx, endidx):
        if not text:
            completions = self.FIRMWARE[:]
        else:
            completions = [f
                           for f in self.FIRMWARE
                           if f.startswith(text)
                           ]
        return completions

    def do_help(self, arg):
        values = arg.split(' ')
        if len(values) == 1 and values[0] == '':
            help_title = Style.BRIGHT + Fore.MAGENTA + "uArm Command line Help Center" + Fore.RESET + Style.RESET_ALL
            help_title += "\n\n"
            help_title += "Please use {}{}connect{}{} before any control action".format(Back.BLACK, Fore.WHITE, Fore.RESET, Back.RESET)
            help_title += "\n"
            help_title += self.help_msg
            print (help_title)
        # print (self.help_msg)
        Cmd.do_help(self,arg)

    def do_quit(self, args):
        """
        Quit, if uarm is connected, will disconnect before quit
        """
        if self.uarm is not None:
            if self.uarm.is_connected():
                self.uarm.disconnect()
        print ("Quiting")
        raise SystemExit

    do_EOF = do_quit


# class SerialMode(Cmd):
#     prompt = "Serial >>> "
#     intro = "Welcome to Serial Mode."
#     uarm = None
#
#     def __init__(self, uarm):
#         Cmd.__init__(self)
#         self.uarm = uarm
#
#     def default(self, line):
#         if self.uarm.is_connected():
#             response = self.uarm.send_cmd(line)
#             print (response)
#
#     def do_quit(self, args):
#         return True
#
#     do_EOF = do_quit


def main():
    try:
        uarm_cmd = UArmCmd()
        uarm_cmd.cmdloop()
    except KeyboardInterrupt:
        print ("KeyboardInterrupt")

if __name__ == '__main__':
    main()
