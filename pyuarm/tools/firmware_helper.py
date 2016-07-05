#!/usr/bin/env python
#
# This is a module that help user to manage the uArm firmware.
# Please use -h to list all parameters of this script

# This file is part of pyuarm. https://github.com/uArm-Developer/pyuarm
# (C) 2016 UFACTORY <developer@ufactory.cc>

import pyuarm
from pyuarm.tools.list_uarms import uarm_ports
from progressbar import ProgressBar, Percentage, FileTransferSpeed, Bar, ETA
import requests
import os, sys, platform, subprocess
from itertools import izip
import ConfigParser, StringIO

from distutils.version import LooseVersion
import argparse

firmware_download_url = "http://download.ufactory.cc/firmware.hex"
remote_version_url = "http://download.ufactory.cc/version"


def get_uarm_port():
    uarm_list = uarm_ports()
    if len(uarm_list) > 0:
        return uarm_list[0]
    else:
        print "No uArm is connected."


class FirmwareHelper():
    firmware_defaul_filename = 'firmware.hex'
    application_path = ""
    firmware_path = ""
    remote_firmware_version = ""
    uarm_firmware_version = ""
    uarm_port = get_uarm_port()

    def __init__(self):
        self.remote_firmware_version = "0.0.0"
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
        elif __file__:
            self.application_path = os.path.dirname(__file__)
        self.firmware_path = os.path.join(os.getcwd(), self.firmware_defaul_filename)

    def flash_firmware(self, firmware_path='firmware.hex', port=uarm_port):
        if port:
            global avrdude_path, error_description, cmd
            port_conf = '-P' + port
            if platform.system() == 'Darwin':
                cmd = ['avrdude', '-v', '-patmega328p', '-carduino', port_conf, '-b115200', '-D',
                   '-Uflash:w:{0}:i'.format(firmware_path)]
                error_description = "avrdude is required, Trying to install avrdude..."

            elif platform.system() == 'Windows':
                exe_name = 'avrdude.exe'
                conf_name = 'avrdude.conf'
                avrdude_path = os.path.join(self.application_path, 'avrdude', exe_name)
                avrdude_conf = os.path.join(self.application_path, 'avrdude', conf_name)
                cmd = [avrdude_path, '-C' + avrdude_conf, '-v', '-patmega328p', '-carduino', port_conf, '-b115200', '-D',
                   '-Uflash:w:{0}:i'.format(firmware_path)]

            elif platform.system() == 'Linux':
                cmd = ['avrdude', '-v', '-patmega328p', '-carduino', port_conf, '-b115200', '-D',
                   '-Uflash:w:{0}:i'.format(firmware_path)]
                error_description = "avrdude is required, Trying to install avrdude"

            print (' '.join(cmd))
            try:
                subprocess.call(cmd)
            except OSError as e:
                print ("Error occurred: error code {0}".format(str(e.errno)))
                if e.errno == 2:
                    if platform.system() == 'Darwin':
                        try:
                            print ("Installing avrdude...")
                            subprocess.call(['brew', 'install', 'avrdude'])
                            subprocess.call(cmd)
                        except OSError as e:
                            print ("Error occurred: error code {0}".format(str(e.errno)))
                            if e.errno == 2:
                                print ("-------------------------------------------------------")
                                print ("You didn't install homebrew, please visit http://bew.sh")
                                print ("-------------------------------------------------------")
                    if platform.system() == 'Linux':
                        print ("------------------------------------------------------------------------------")
                        print ("You didn't install avrdude.\n "
                               "please try `sudo apt-get install avrdude` or other package management command ")
                        print ("------------------------------------------------------------------------------")

    def download_firmware(self, firmware_url=firmware_download_url):
        print ("Downloading firmware.hex...")
        try:
            response = requests.get(firmware_url, stream=True)
            firmware_size = int(response.headers['content-length'])
            with open(self.firmware_path, "wb") as handle:
                widgets = ['Downloading: ', Percentage(), ' ',
                           Bar(marker='#', left='[', right=']'),
                           ' ', ETA(), ' ', FileTransferSpeed()]
                pbar = ProgressBar(widgets=widgets, maxval=firmware_size)
                pbar.start()
                for i, data in izip(range(firmware_size), response.iter_content()):
                    handle.write(data)
                    pbar.update(i)
                pbar.finish()
        except requests.exceptions.ConnectionError:
            raise NetworkError("NetWork Error, Please retry...")

    def get_latest_version(self, release_url=remote_version_url):
        try:
            r = requests.get(release_url)
            s_config = r.text
            buf = StringIO.StringIO(s_config)
            config = ConfigParser.ConfigParser()
            config.readfp(buf)
            self.remote_firmware_version = config.get('firmware', 'version')
            # print("Remote Version: {0}".format(self.remote_firmware_version))
        except requests.exceptions.ConnectionError:
            raise NetworkError("NetWork Error, Please retry...")

    def get_uarm_version(self):
        if self.uarm_port is not None or self.uarm_port != "":
            print ("Reading Firmware version from uArm...")
            try:
                uarm = pyuarm.uArm(port=self.uarm_port)
                self.uarm_firmware_version = uarm.firmware_version
                uarm.disconnect()
            except pyuarm.UnkwonFirmwareException:
                print "Unknown Firmware version."
            except pyuarm.NoUArmPortException:
                print "No uArm is connected."

    def comapre_version(self):
        self.get_latest_version()
        self.get_uarm_version()
        if LooseVersion(self.remote_firmware_version) > LooseVersion(self.uarm_firmware_version):
            return True


def main():
    """
    ::

        $ uarm-firmware -h

        usage: firmware_helper [-h] [-d] [-f [FORCE]] [-c [CHECK]] [-p [PORT]]

        optional arguments:
          -h, --help            show this help message and exit
          -d, --download        download firmware into firmware.hex
          -f [FORCE], --force [FORCE]
                                without firmware path, flash default firmware.hex,
                                with firmware path, flash the firmware, eg. -f
                                Blink.ino.hex
          -c [CHECK], --check [CHECK]
                                remote - lateset firmware release version, local -
                                read uArm firmware version
          -p [PORT], --port [PORT]
                                provide port number
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--download", help="download firmware into firmware.hex", action="store_true")
    parser.add_argument("-f", "--force", nargs='?', const='force',
                        help="without firmware path, flash default firmware.hex, with firmware path, flash the firmware, eg. -f Blink.ino.hex")
    parser.add_argument("-c", "--check", nargs='?', const='local',
                        help="remote - lateset firmware release version, local - read uArm firmware version")
    parser.add_argument("-p", "--port", nargs='?', help="provide port number")
    args = parser.parse_args()
    helper = FirmwareHelper()

    # download
    if args.download:
        try:
            helper.download_firmware()
        except NetworkError as e:
            print (e.error)
        except APIError as e:
            print (e.error)
        sys.exit(0)
    # force
    if args.force == "force":
        if not os.path.exists(helper.firmware_path):
            print "firmware.hex not existed"
        else:
            if args.port:
                helper.flash_firmware(port=args.port)
            else:
                helper.flash_firmware()
        sys.exit(0)
    elif args.force is not None and args.force != "":
        if not os.path.exists(args.force):
            print args.force + " not existed."
        else:
            if args.port:
                helper.flash_firmware(firmware_path=args.force,port=args.port)
            else:
                helper.flash_firmware(firmware_path=args.force)
            sys.exit(0)
    # check
    if args.check == "local":
        if helper.uarm_port is None or helper.uarm_port == "":
            sys.exit(0)
        helper.get_uarm_version()
        sys.exit(0)
    elif args.check == "remote":
        print "Fetching the remote version..."
        helper.get_latest_version()
        print "Latest firmware release version is: {0}".format(helper.remote_firmware_version)
        sys.exit(0)

    if helper.uarm_port is None or helper.uarm_port == "":
        sys.exit(0)

    # No Argument#####
    try:
        version_compare = helper.comapre_version()
        print "Latest Firmware version: {0}".format(helper.remote_firmware_version)
        # print "Your uArm Firmware version: {0}".format(helper.uarm_firmware_version)
        if version_compare:
            print ("Would you want to upgrade your uArm with {0}{1}".format(helper.remote_firmware_version, "?"))
            user_choice = raw_input("Please Enter Y if yes. ")
            if user_choice == "Y" or user_choice == "y":
                try:
                    helper.download_firmware()
                except NetworkError as e:
                    print (e.error)
                except APIError as e:
                    print (e.error)
                # args.port:
                if args.port:
                    helper.flash_firmware(port=args.port)
                else:
                    helper.flash_firmware()
            else:
                sys.exit(0)
        else:
            print("You already have the latest version of Firmware installed in uArm!!!")
            print("If you still want to download & flash the firmware, Please use `uarm-firmware -d ; uarm-firmware -f`")
            sys.exit(0)
    except Exception:
        print "Latest Firmware version: {0} ".format(helper.remote_firmware_version)
        print ("Unknown uArm Firmware version, Would you want to upgrade your uArm with {0}{1}".format(helper.remote_firmware_version, "?"))
        user_choice = raw_input("Please Enter Y if yes. ")
        if user_choice == "Y" or user_choice == "y":
            try:
                helper.download_firmware()
            except NetworkError as e:
                print (e.error)
            except APIError as e:
                print (e.error)
            # args.port:
            if args.port:
                helper.flash_firmware(port=args.port)
            else:
                helper.flash_firmware()
        else:
            sys.exit(0)


def exit_fun():
    raw_input("\nPress Enter to Exit...")
    sys.exit(0)


class NetworkError(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return repr(self.error)


class APIError(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return repr(self.error)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        exit_fun()
