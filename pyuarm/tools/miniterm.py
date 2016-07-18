#!/usr/bin/env python
#
# This is a module that help user to control your uArm.
# Please use -h to list all parameters of this script

# This file is part of pyuarm. https://github.com/uArm-Developer/pyuarm
# (C) 2016 UFACTORY <developer@ufactory.cc>


import pyuarm
from pyuarm.tools.list_uarms import uarm_ports
import argparse
import logging

logging.basicConfig(filename='logger.log', level=logging.INFO)

logging.info("------------------------------------")


class MiniTerm():

    def __init__(self, port=None, debug=None):
        if port is not None:
            self.port = port
            if debug is not None:
                self.uarm = pyuarm.UArm(port, debug)
            else:
                self.uarm = pyuarm.UArm(port)
        else:
            self.uarm = pyuarm.get_uarm()
            if debug is not None:
                self.uarm.debug = debug

    def loop(self):
        print ("Please input command:")
        while True:
            line = raw_input()
            # logging.info(line)
            # self.output_line(with_prefix=False)
            # strs = ""
            values = line.split(' ')
            if values[0] == '':
                self.output()
            elif values[0].lower() == 'mv':
                if len(values) == 4:
                    result = self.uarm.move_to(int(values[1]), int(values[2]), int(values[3]))
                    msg = "Move to X:{} Y:{} Z:{}".format(int(values[1]),int(values[2]), int(values[3]))
                    if result:
                        self.output(msg)
                    else:
                        self.output("Fail on {}".format(msg))
                else:
                    self.output("argument number not correct, must be: mv number1 number2 number3")
            elif values[0].lower() == 'pump':
                if len(values) == 2:
                    if values[1].lower() == 'on':
                        result = self.uarm.pump_on()
                    elif values[1].lower() == 'off':
                        result = self.uarm.pump_off()
                    else:
                        self.output("argument not correct: {}".format(values[1]))
                        return False
                    self.output("Succeed" if result else "Fail")
                else:
                    self.output("argument number not correct, must be: pump on or pump off")
            else:
                self.output("command not found: {}".format(values[0]))

    def output(self, msg=""):
        print(msg)


def main():
    miniterm = MiniTerm()
    miniterm.loop()

if __name__ == '__main__':
    main()

