#!/usr/bin/env python
#
# This is a module that help user to control your uArm.
# Please use -h to list all parameters of this script

# This file is part of pyuarm. https://github.com/uArm-Developer/pyuarm
# (C) 2016 UFACTORY <developer@ufactory.cc>


import pyuarm
from cmd import Cmd
import logging
from pyuarm.tools.list_uarms import uarm_ports
from pyuarm.tools import firmware_helper
import subprocess

logging.basicConfig(filename='logger.log', level=logging.INFO)

logging.info("------------------------------------")


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class UArmCmd(Cmd):

    prompt = ">>> "
    intro = "Welcome to use {}uArm Command Line{}, please input {}help{} for usage"\
        .format(bcolors.BOLD, bcolors.ENDC, bcolors.UNDERLINE,bcolors.ENDC)

    doc_header = "uArm Console help center"
    ruler = '-'

    uarm = None

    def __init__(self,  *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)

    def __is_connected(self):
        if self.uarm is None:
            print ("No uArm is connected, please use {}")
            return False

    def do_connect(self, arg):
        """
        connect, Open uArm Port, if more than one uArm Port found, will prompt options to choose.
        Please connect to uArm before you do any control action
        """
        if self.uarm is None:
            ports = uarm_ports()
            if len(ports) > 2:
                i = 1
                for port in ports:
                    print ("[{}] - {}".format(i, port))
                    i += 1
                port_index = raw_input("Please Choose the uArm Port: ")
                uarm_port = ports[int(port_index) - 1]
                self.uarm = pyuarm.UArm(uarm_port)
            if len(ports) == 1:
                self.uarm = pyuarm.UArm()
            if len(ports) == 0:
                print ("No uArm Connected")
        else:
            self.uarm.reconnect()

    def do_disconnect(self,arg):
        """
        disconnect, Release uarm port.
        """
        if self.uarm is not None:
            if self.uarm.is_connected():
                self.uarm.disconnect()
                print ("uArm {} disconnect.".format(self.uarm.port))

    def do_move_to(self, arg):
        """
        move_to, move to destination coordinate.
        format: move_to X Y Z or move_to X Y Z S
        X,Y,Z unit millimeter, S means Speed, unit mm/s
        eg. move_to 100 200 150
        """
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

    def do_get_coordinate(self, arg):
        coords = self.uarm.get_coordinate()
        print (coords)

    def do_pump(self, arg):
        if arg == 'on':
            self.uarm.pump_on()
        elif arg == 'off':
            self.uarm.pump_off()

    def do_sim(self, arg):
        values = arg.split(' ')
        if len(values) == 3:
            result = self.uarm.get_simulation(int(values[0]), int(values[1]), int(values[2]))
            msg = "succeed" if result else "failed"
            print (msg)

    def do_write_angle(self, arg):
        values = arg.split(' ')
        if len(values) == 3:
            servo_num = int(values[0])
            angle = float(values[1])
            result = self.uarm.set_servo_angle(servo_num, angle)
            msg = "succeed" if result else "failed"
            print (msg)

    def do_read_angle(self, arg):
        values = arg.split(' ')
        if len(values) == 1:
            if values[0] == '':
                angles = self.uarm.get_servo_angle()
                print (angles)
            else:
                servo_num = int(values[0])
                angle = self.uarm.get_servo_angle(servo_num)
                print (angle)

    def do_alert(self, arg):
        values = arg.split(' ')
        if len(values) == 2:
            frequency = int(values[0])
            duration = int(values[1])
            result = self.uarm.set_buzzer(frequency,duration)
            msg = "succeed" if result else "failed"
            print (msg)

    def do_set_polar(self, arg):
        values = arg.split(' ')
        if len(values) == 4:
            result = self.uarm.set_polar(values[0], values[1], values[2], values[3])
            msg = "succeed" if result else "failed"
            print (msg)

    def do_get_polar(self, arg):
        result = self.uarm.get_polar()
        if result:
            print ("polar coordinate: {}".format(result))

    def do_servo(self, arg):
        values = arg.split(' ')
        if len(values) == 2:
            if values[0] == 'attach':
                if values[1] == 'all':
                    self.uarm.servo_attach()

    # def do_test(self, arg1):
    #     print arg1

    FIRMWARE =['version', 'force', 'upgrade']

    def do_firmware(self, arg):
            if arg == 'version':
                print ("Local Firmware Version: {}".format(self.uarm.firmware_version))
                print ("Remote Firmware Version: {}".format(firmware_helper.get_latest_version()))
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

    def do_EOF(self, args):
        """
        Quit, if uarm is connected, will disconnect before quit
        """
        if self.uarm is not None:
            if self.uarm.is_connected():
                self.uarm.disconnect()
        print ("Quiting")
        raise SystemExit


def main():

    uarm_cmd = UArmCmd()
    uarm_cmd.cmdloop()

if __name__ == '__main__':
    main()

