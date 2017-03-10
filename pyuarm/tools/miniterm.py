#!/usr/bin/env python
#
# This is a module that help user to control your uArm.
# Please use -h to list all parameters of this script

# This file is part of pyuarm. https://github.com/uArm-Developer/pyuarm
# (C) 2016 UFACTORY <developer@ufactory.cc>


from cmd import Cmd
from .list_uarms import get_uarm_port_cli, uarm_ports
from ..uarm import UArm, UArmConnectException
from ..log import DEBUG, printf

version = "0.1.6"


class UArmCmd(Cmd):
    help_msg = "Shortcut:" + "\n"
    help_msg += "Quit: " + "Ctrl + D"
    help_msg += ", or input: " + "quit" + "\n"
    help_msg += "Clear Screen: " + "Ctrl + L"

    ON_OFF = ['on', 'off']

    FIRMWARE = ['version', 'force', 'upgrade']

    SERVO_STATUS = ['attach', 'detach']

    prompt = ">>> "
    intro = "Welcome to use uArm Command Line - v{}\n" \
        .format(version)

    intro += help_msg
    intro += "\n\n"
    intro += "Input help for more usage"

    # doc_header = "documented commands:"
    ruler = '-'

    arm = None

    def __init__(self, port=None, debug=False, *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)
        self.__connect(port=port, debug=debug)

    def __is_connected(self):
        if self.arm is None:
            print("No uArm is connected, please use connect")
            return False
        else:
            if self.arm.connection_state:
                return True
            else:
                print("No uArm is connected, please use connect command")
                return False

    def do_connect(self, arg):
        """
        connect, Open uArm Port, if more than one uArm Port found, will prompt options to choose.
        Please connect to uArm before you do any control action
        """
        if len(arg) != 0:
            self.__connect(arg)
        elif len(arg) == 0:
            self.__connect()

    def __connect(self, port=None, debug=False, timeout=1):
        """
        connect uArm.
        :param port:
        :param debug:
        :return:
        """

        if self.arm is None:
            if port is not None:
                self.arm = UArm(port_name=port, debug=debug, timeout=timeout)
            else:
                ports = uarm_ports()
                if len(ports) > 1:
                    uarm_port = get_uarm_port_cli()
                    try:
                        self.arm = UArm(port_name=uarm_port, debug=debug, timeout=timeout)
                    except UArmConnectException as e:
                        print("uArm Connect failed, {}".format(str(e)))
                elif len(ports) == 1:
                    self.arm = UArm(debug=debug, timeout=timeout)
                    self.arm.connect()
                elif len(ports) == 0:
                    print("No uArm ports is found.")
        else:
            if self.arm.connection_state:
                print("uArm is already connected, port: {}".format(self.arm.port_name))
            else:
                if self.arm.connect():
                    print("uArm port: {} is reconnected")

    def do_disconnect(self, arg):
        """
        disconnect, Release uarm port.
        """
        if self.arm is not None:
            if self.arm.connection_state:
                self.arm.disconnect()

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
                result = self.arm.set_position(int(values[0]), int(values[1]), int(values[2]), wait=True)
                # msg = "succeed" if result else "failed"
                # print(msg)
            elif len(values) == 4:
                result = self.arm.set_position(int(values[0]), int(values[1]), int(values[2]), speed=int(values[3]), wait=True)
                # msg = "succeed" if result else "failed"
                # print(msg)

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
            coords = self.arm.get_position()
            print("Current coordinate: X:{} Y:{} Z:{}".format(*coords))

    def do_pump(self, arg):
        """
        pump
        turn on/off pump
        """
        if self.__is_connected():
            if arg == 'on':
                result = self.arm.set_pump(True, wait=True)
                print("succeed" if result else "failed")
            elif arg == 'off':
                result = self.arm.set_pump(False, wait=True)
                print("succeed" if result else "failed")
            elif arg == '':
                print("please input argument: {}".format(','.join(self.ON_OFF)))
            else:
                print("Command not found {}".format(arg))

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
    #             result = self.arm.get_simulation(int(values[0]), int(values[1]), int(values[2]))
    #             msg = "succeed" if result else "failed"
    #             print (msg)

    def do_set_angle(self, arg):
        """
        set_angle
        format: write_angle servo_number angle
        servo_number:
        - 0 bottom servo,
        - 1 left servo,
        - 2 right servo,
        - 3 hand servo
        eg.
        >>> set_angle 0 90
        succeed
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                servo_num = int(values[0])
                angle = float(values[1])
                result = self.arm.set_servo_angle(servo_num, angle, wait=True)
                msg = "succeed" if result else "failed"
                print(msg)

    def do_get_angle(self, arg):
        """
        get_angle
        Read current servo angle.
        format: read_angle servo_number
        servo_number:
        - 0 bottom servo,
        - 1 left servo,
        - 2 right servo,
        if no servo_number provide, will list all servos angle
        eg.
        >>> get_angle
        Current Servo Angles: b:17.97, l:112.72, r:17.97, h:151.14
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 1:
                if values[0] == '':
                    angles = self.arm.get_servo_angle()
                    print("Current Servo Angles: t:{}, l:{}, r:{}, h:{}".format(*angles))

                else:
                    servo_num = int(values[0])
                    angle = self.arm.get_servo_angle(servo_num)
                    print(angle)

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
                result = self.arm.set_buzzer(frequency, duration, wait=True)
                msg = "succeed" if result else "failed"
                print(msg)

    # def do_set_polar(self, arg):
    #     if self.__is_connected():
    #         values = arg.split(' ')
    #         if len(values) == 4:
    #             result = self.arm.set_polar_coordinate(values[0], values[1], values[2], values[3])
    #             msg = "succeed" if result else "failed"
    #             print (msg)
    #         if len(values) == 3:
    #             result = self.arm.set_polar_coordinate(values[0], values[1], values[2])
    #             msg = "succeed" if result else "failed"
    #             print (msg)
    #
    # def do_get_polar(self, arg):
    #     if self.__is_connected():
    #         result = self.arm.get_polar_coordinate()
    #         if result:
    #             print ("polar coordinate: {}".format(result))

    def do_servo(self, arg):
        """
        Servo status
        format:
        - servo attach servo_number
        - servo detach servo_number
        servo_number:
        - 0 bottom servo,
        - 1 left servo,
        - 2 right servo,
        - 3 hand servo
        - all
        eg.
        - servo attach all
        - servo detach all
        """
        if self.__is_connected():
            values = arg.split(' ')
            if len(values) == 2:
                if values[0] == 'attach':
                    if values[1] == 'all':
                        self.arm.set_servo_attach()
                    elif values[1].isdigit():
                        v = int(values[1])
                        if 0 <= v <= 3:
                            self.arm.set_servo_attach(v)
                elif values[0] == 'detach':
                    if values[1] == 'all':
                        self.arm.set_servo_detach()
                    elif values[1].isdigit():
                        v = int(values[1])
                        if 0 <= v <= 3:
                            self.arm.set_servo_detach(v)

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
            serial_mode = SerialMode(self.arm)
            serial_mode.cmdloop()

    def do_help(self, arg):
        values = arg.split(' ')
        if len(values) == 1 and values[0] == '':
            help_title = "uArm Command line Help Center"
            help_title += "\n\n"
            help_title += "Please use connect before any control action"
            help_title += "\n"
            help_title += self.help_msg
            print(help_title)
        # print (self.help_msg)
        Cmd.do_help(self, arg)

    def do_quit(self, args):
        """
        Quit, if uarm is connected, will disconnect before quit
        """
        if self.arm is not None:
            if self.arm.connection_state:
                self.arm.disconnect()
        print("Quiting")
        raise SystemExit

    do_EOF = do_quit


class SerialMode(Cmd):
    prompt = "Serial >>> "
    intro = "Welcome to Serial Mode."
    uarm = None

    def __init__(self, uarm):
        Cmd.__init__(self)
        self.arm = uarm

    def default(self, line):
        if self.arm.connection_state:
            try:
                serial_id, response = self.arm.send_and_receive(line)
                # print(serial_id, response)
                print("${} {}".format(serial_id, ' '.join(response)))
            except TypeError as e:
                print("Command not correct")
                printf("Error: {}".format(e), DEBUG)

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
        print("KeyboardInterrupt")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="specify port number")
    parser.add_argument("-d", "--debug", help="Open Debug Message")
    args = parser.parse_args()
    main(args)
