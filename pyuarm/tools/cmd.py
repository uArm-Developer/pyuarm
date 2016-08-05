#!/usr/bin/env python
#
# This is a module that help user to control your uArm.
# Please use -h to list all parameters of this script

# This file is part of pyuarm. https://github.com/uArm-Developer/pyuarm
# (C) 2016 UFACTORY <developer@ufactory.cc>


import pyuarm
from cmd2 import Cmd
import logging
from pyuarm.tools.list_uarms import uarm_ports
from pyuarm.tools import firmware_helper
import subprocess

logging.basicConfig(filename='logger.log', level=logging.INFO)

logging.info("------------------------------------")


class UArmCmd(Cmd):

    prompt = ">>> "
    uarm = None

    def __init__(self,  *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)

    def do_connect(self, arg):
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
        if self.uarm is not None:
            if self.uarm.is_connected():
                self.uarm.disconnect()
                print ("uArm {} disconnect.".format(self.uarm.port))

    def do_move_to(self, arg):
        values = arg.split(' ')
        if len(values) == 3:
            result = self.uarm.move_to(int(values[0]), int(values[1]), int(values[2]))
            msg = "succeed" if result else "failed"
            print (msg)
        elif len(values) == 4:
            result = self.uarm.move_to(int(values[0]), int(values[1]), int(values[2]), int(values[3]))
            msg = "succeed" if result else "failed"
            print (msg)

    def do_read_coordiante(self,arg):
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
            result = self.uarm.validate_coordinate(int(values[0]), int(values[1]), int(values[2]))
            msg = "succeed" if result else "failed"
            print (msg)

    def do_write_angle(self, arg):
        values = arg.split(' ')
        if len(values) == 3:
            servo_num = int(values[0])
            angle = float(values[1])
            result = self.uarm.write_servo_angle(servo_num,angle)
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

    def do_firmware(self, arg):
        values = arg.split(' ')
        if len(values) == 1:
            if values[0] == 'local':
                print ("Local Firmware Version: {}".format(self.uarm.firmware_version))
            elif values[0] == 'remote':
                print ("Remote Firmware Version: {}".format(firmware_helper.get_latest_version()))
            elif values[0] == 'upgrade':
                if self.uarm is not None:
                    if self.uarm.is_connected():
                        self.uarm.disconnect()
                    subprocess.call(['uarm-firmware','-u', '-p', self.uarm.port])
                else:
                    subprocess.call(['uarm-firmware','-u'])
            elif values[0] == 'force':
                if self.uarm is not None:
                    if self.uarm.is_connected():
                        self.uarm.disconnect()
                    subprocess.call(['uarm-firmware','-d', '-f', '-p', self.uarm.port])
                else:
                    subprocess.call(['uarm-firmware','-df'])
            elif values[0] == '':
                print ("please input argument: local, remote, upgrade, force")
            else:
                print ("command not found: {}".format(values[0]))


def main():

    uarm_cmd = UArmCmd()
    uarm_cmd.cmdloop()

    # uarm_cmd = UArmCmd()
    # uarm_cmd.cmdloop()

if __name__ == '__main__':
    main()

