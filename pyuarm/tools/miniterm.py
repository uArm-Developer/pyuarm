#!/usr/bin/env python
#
# This is a module that help user to control your uArm.
# Please use -h to list all parameters of this script

# This file is part of pyuarm. https://github.com/uArm-Developer/pyuarm
# (C) 2016 UFACTORY <developer@ufactory.cc>


from cmd import Cmd
from .list_uarms import get_uarm_port_cli, uarm_ports
from ..uarm import UArm
from .. import util

version = "0.1.4"


class UArmCmd(Cmd):

    help_msg = "Shortcut:" + "\n"
    help_msg += "Quit: " + "Ctrl + D"
    help_msg += ", or input: " + "quit" + "\n"
    help_msg += "Clear Screen: " + "Ctrl + L"

    ON_OFF = ['on', 'off']

    FIRMWARE =['version', 'force', 'upgrade']

    SERVO_STATUS = ['attach', 'detach']

    prompt = ">>> "
    intro = "Welcome to use uArm Command Line - v{}\n"\
        .format(version)

    intro += help_msg
    intro += "\n\n"
    intro += "Input help for more usage"

    # doc_header = "documented commands:"
    ruler = '-'

    uarm = None

    def __init__(self, port=None,debug=False, *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)
        self.connect(port=port,debug=debug)

    def __is_connected(self):
        if self.uarm is None:
            print ("No uArm is connected, please use connect")
            return False
        else:
            if self.uarm.is_connected():
                return True
            else:
                print ("No uArm is connected, please use connect command")
                return False

    def do_connect(self, arg):
        """
        connect, Open uArm Port, if more than one uArm Port found, will prompt options to choose.
        Please connect to uArm before you do any control action
        """
        if len(arg) != 0:
            self.connect(arg)
        elif len(arg) == 0:
            self.connect()

    def connect(self, port=None, debug=False):
        """
        connect uArm.
        :param port:
        :return:
        """

        if self.uarm is None:
            if port is not None:
                self.uarm = UArm(port_name=port, debug=debug)
            else:
                ports = uarm_ports()
                if len(ports) > 1:
                    uarm_port = get_uarm_port_cli()
                    try:
                        self.uarm = UArm(uarm_port)
                    except util.UArmConnectException as e:
                        print ("uArm Connect failed, {}".format(str(e)))
                elif len(ports) == 1:
                    self.uarm = UArm()
                elif len(ports) == 0:
                    print ("No uArm ports is found.")
        else:
            if self.uarm.is_connected():
                print ("uArm is already connected, port: {}".format(self.uarm.port.device))
            else:
                if self.uarm.connect():
                    print ("uArm port: {} is reconnected")

    def do_disconnect(self,arg):
        """
        disconnect, Release uarm port.
        """
        if self.uarm is not None:
            if self.uarm.is_connected():
                self.uarm.disconnect()

    def do_set_position(self, arg):
        """
        set_position, move to destination coordinate.
        format: set_position X Y Z or move_to X Y Z S
        X,Y,Z unit millimeter, S means Speed, unit mm/s
        eg. set_position 100 200 150
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 3:
                result = self.uarm.set_position(int(values[0]), int(values[1]), int(values[2]))
                msg = "succeed" if result else "failed"
                print (msg)
            elif len(values) == 4:
                result = self.uarm.set_position(int(values[0]), int(values[1]), int(values[2]), int(values[3]))
                msg = "succeed" if result else "failed"
                print (msg)

    def do_sp(self, args):
        """
        same with set_position
        """
        self.do_set_position(args)

    def do_get_position(self, arg):
        """
        get_position get current coordinate
        """
        if self.__is_connected():
            coords = self.uarm.get_position()
            print ("Current coordinate: X:{} Y:{} Z:{}".format(*coords))

    def do_pump(self, arg):
        """
        pump
        turn on/off pump
        """
        if self.__is_connected():
            if arg == 'on':
                result = self.uarm.set_pump(True)
                print ("succeed" if result else "failed")
            elif arg == 'off':
                result = self.uarm.set_pump(False)
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

    def do_sim(self, arg):
        """
        sim
        format: sim X Y Z
        validate the coordinate.
        eg. sim 100 200 100
        succeed
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 3:
                result = self.uarm.get_simulation(int(values[0]), int(values[1]), int(values[2]))
                msg = "succeed" if result else "failed"
                print (msg)

    def do_set_angle(self, arg):
        """
        set_angle
        format: write_angle servo_number angle
        servo_number:
            0 bottom servo,
            1 left servo,
            2 right servo,
            3 hand servo
        eg.
        >>> set_angle 0 90
        succeed
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                servo_num = int(values[0])
                angle = float(values[1])
                result = self.uarm.set_servo_angle(servo_num, angle)
                msg = "succeed" if result else "failed"
                print (msg)

    def do_get_angle(self, arg):
        """
        get_angle
        Read current servo angle.
        format: read_angle servo_number
        servo_number:
            0 bottom servo,
            1 left servo,
            2 right servo,
        if no servo_number provide, will list all servos angle
        eg.
        >>> get_angle
        Current Servo Angles: b:17.97, l:112.72, r:17.97, h:151.14
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 1:
                if values[0] == '':
                    angles = self.uarm.get_servo_angle()
                    print ("Current Servo Angles: t:{}, l:{}, r:{}, h:{}".format(*angles))

                else:
                    servo_num = int(values[0])
                    angle = self.uarm.get_servo_angle(servo_num)
                    print (angle)

    def do_alert(self, arg):
        """
        alert
        control buzzer
        format: alert frequency duration
        eg.
        alert 1 1
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                frequency = int(values[0])
                duration = float(values[1])
                result = self.uarm.set_buzzer(frequency, duration)
                msg = "succeed" if result else "failed"
                print (msg)

    # def do_set_polar(self, arg):
    #     if self.__is_connected():
    #         values = arg.split(' ')
    #         if len(values) == 4:
    #             result = self.uarm.set_polar_coordinate(values[0], values[1], values[2], values[3])
    #             msg = "succeed" if result else "failed"
    #             print (msg)
    #         if len(values) == 3:
    #             result = self.uarm.set_polar_coordinate(values[0], values[1], values[2])
    #             msg = "succeed" if result else "failed"
    #             print (msg)
    #
    # def do_get_polar(self, arg):
    #     if self.__is_connected():
    #         result = self.uarm.get_polar_coordinate()
    #         if result:
    #             print ("polar coordinate: {}".format(result))

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
                        self.uarm.set_servo_attach()
                    elif values[1].isdigit():
                        v = int(values[1])
                        if 0 <= v <= 3:
                            self.uarm.set_servo_attach(v)
                elif values[0] == 'detach':
                    if values[1] == 'all':
                        self.uarm.set_servo_detach()
                    elif values[1].isdigit():
                        v = int(values[1])
                        if 0 <= v <= 3:
                            self.uarm.set_servo_detach(v)

    def complete_servo(self, text, line, begidx, endidx):
        if not text:
            completions = self.SERVO_STATUS[:]
        else:
            completions = [f
                           for f in self.SERVO_STATUS
                           if f.startswith(text)
                           ]
        return completions

    def do_serial(self, arg):
        """
        Raw Serial Mode
        You could direct input the communication protocol here.
        """
        if self.__is_connected():
            serial_mode = SerialMode(self.uarm)
            serial_mode.cmdloop()

    # def do_firmware(self, arg):
    #     """
    #     Firmware command
    #     sub command: version, upgrade, force
    #     version - display Remote Firmware version and local Firmware version (if connected)
    #     upgrade - if remote version latter than local firmware version, will flash the latest firmware to uarm
    #     force - force upgrade
    #
    #     """
    #     if arg == 'version':
    #         print ("Remote Firmware Version: {}".format(firmware_helper.get_latest_version()))
    #         if self.__is_connected():
    #             print ("Local Firmware Version: {}".format(self.uarm.firmware_version))
    #     elif arg == 'upgrade':
    #         if self.uarm is not None:
    #             if self.uarm.is_connected():
    #                 self.uarm.disconnect()
    #             subprocess.call(['uarm-firmware','-u', '-p', self.uarm.port])
    #         else:
    #             subprocess.call(['uarm-firmware','-u'])
    #     elif arg == 'force':
    #         if self.uarm is not None:
    #             if self.uarm.is_connected():
    #                 self.uarm.disconnect()
    #             subprocess.call(['uarm-firmware','-d', '-f', '-p', self.uarm.port])
    #         else:
    #             subprocess.call(['uarm-firmware','-df'])
    #     elif arg == '':
    #         print ("please input argument: {}".format(','.join(self.FIRMWARE)))
    #     else:
    #         print ("command not found: {}".format(arg))
    #
    # def complete_firmware(self, text, line, begidx, endidx):
    #     if not text:
    #         completions = self.FIRMWARE[:]
    #     else:
    #         completions = [f
    #                        for f in self.FIRMWARE
    #                        if f.startswith(text)
    #                        ]
    #     return completions

    def do_help(self, arg):
        values = arg.split(' ')
        if len(values) == 1 and values[0] == '':
            help_title = "uArm Command line Help Center"
            help_title += "\n\n"
            help_title += "Please use connect before any control action"
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


class SerialMode(Cmd):
    prompt = "Serial >>> "
    intro = "Welcome to Serial Mode."
    uarm = None

    def __init__(self, uarm):
        Cmd.__init__(self)
        self.uarm = uarm

    def default(self, line):
        if self.uarm.is_connected():
            response = self.uarm.send_cmd(line)
            print (response)

    def do_quit(self, args):
        return True

    do_EOF = do_quit

def main(args):
    """
    ::

        python -m pyuarm.tools.miniterm
        pyuarm - INFO - pyuarm version: 2.1.1
        pyuarm - INFO - Connecting from port - /dev/cu.usbserial-A600CRE6...
        pyuarm - INFO - connected...
        pyuarm - INFO - Firmware Version: 2.1.4
        Welcome to use uArm Command Line - v0.1.4
        Shortcut:
        Quit: Ctrl + D, or input: quit
        Clear Screen: Ctrl + L

        Input help for more usage
        >>>

    """
    try:
        uarm_cmd = UArmCmd(port=args.port, debug=args.debug)
        uarm_cmd.cmdloop()
    except KeyboardInterrupt:
        print ("KeyboardInterrupt")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="specify port number")
    parser.add_argument("-d", "--debug", help="Open Debug Message")
    args = parser.parse_args()
    main(args)