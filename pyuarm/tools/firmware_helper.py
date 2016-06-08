#!/usr/bin/env python
import pycurl, certifi
import json
from io import BytesIO
from tqdm import tqdm
import requests
import os, zipfile, sys, platform,subprocess
from pyuarm import *
from distutils.version import LooseVersion, StrictVersion
import argparse

github_release_url = "https://api.github.com/repos/uArm-Developer/FirmwareHelper/releases/latest"
firmware_defaul_filename = 'firmware.hex'
application_path = ""
firmware_path = ""
uarm_port = ""
firmware_url = ""
firmware_size = ""

def update_firmware_path(path):
    global firmware_path
    firmware_path = path

def update_uarm_port(port):
    global uarm_port
    uarm_port = port

def update_firmware_url(url):
    global firmware_url
    firmware_url = url

def update_firmware_size(size):
    global firmware_size
    firmware_size = size

def init():
    global application_path
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    update_firmware_path(os.path.join(os.getcwd(), firmware_defaul_filename))
    get_uarm_port()

def get_uarm_port():
    uarm_list = list_uarms()
    if len(uarm_list) > 0:
        update_uarm_port(uarm_list[0])
        return True
    else:
        print "No uArm is connected."
        sys.exit(0)

def flash_firmware():
    if platform.system() == 'Darwin':
        avrdude_path = 'avrdude'
        conf_name = 'avrdude.conf'
        description = "avrdude is required, Please try `brew install avrdude`"
    elif platform.system() == 'Windows':
        avrdude_path = os.path.join(application_path, 'avrdude', 'avrdude.exe')
        conf_name = 'avrdude_win.conf'
    elif platform.system() == 'Linux':
        avrdude_path = 'avrdude'
        conf_name = 'avrdude.conf'
        description =  "avrdude is required, Please try `apt-get install avrdude`"

    avrdude_conf = os.path.join(application_path, 'avrdude', conf_name)
    port = '-P' + uarm_port
    cmd = [avrdude_path, '-C'+avrdude_conf, '-v', '-patmega328p', '-carduino', port, '-b115200', '-D', '-Uflash:w:'+ firmware_path +':i']
    print ' '.join(cmd)
    try:
        subprocess.call(cmd)
    except OSError:
        print description

def get_download_url():
    url = github_release_url
    c = pycurl.Curl()
    data = BytesIO()
    c.setopt(pycurl.CAINFO, certifi.where())
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, data.write)
    c.perform()
    dict = json.loads(data.getvalue())
    firmware_url = dict['assets'][0]['browser_download_url']
    firmware_size = dict['assets'][0]['size']
    update_firmware_url(firmware_url)
    update_firmware_size(firmware_size)
    print firmware_url

def download_firmware():
    print ("Downloading firmware.hex...")
    get_download_url()
    response = requests.get(firmware_url, stream=True)
    with open(firmware_path, "wb") as handle:
        for data in tqdm(response.iter_content(), total=firmware_size):
            handle.write(data)

def get_latest_version():
    global web_firmware_version
    url = github_release_url
    c = pycurl.Curl()
    data = BytesIO()
    c.setopt(pycurl.CAINFO, certifi.where())
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, data.write)
    c.perform()
    dict = json.loads(data.getvalue())
    version = dict['tag_name']
    web_firmware_version = version

def get_uarm_version():
    global uarm_firmware_version
    print "Reading Firmware version from uArm..."
    try:
        uarm = uArm(port=uarm_port)
        uarm_firmware_version = uarm.firmware_version
        uarm.disconnect()
    except:
        print "Unknown Firmware version."

def comapre_version():
    get_latest_version()
    get_uarm_version()
    if LooseVersion(web_firmware_version) > LooseVersion(uarm_firmware_version):
        return True

def main():
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--download" , help="download firmware into firmware.hex", action="store_true")
    parser.add_argument("-f", "--flash", nargs='?', const='download',help="without firmware path, flash default firmware.hex, if not existed, download automatically, with firmware path, flash the firmware, eg. -f Blink.ino.hex")
    parser.add_argument("-c", "--check", nargs='?', const='local', help="remote - lateset firmware release version, local - read uArm firmware version")
    args = parser.parse_args()
    #download
    if args.download:
        download_firmware()
        sys.exit(0)
    #flash
    if args.flash == "download":
        if not os.path.exists(firmware_path):
            print "firmware not existed, Downloading..."
            download_firmware()
        get_uarm_port()
        flash_firmware()
        sys.exit(0)
    elif args.flash is not None and args.flash !="" :
        if not os.path.exists(args.flash):
            print args.flash + " not existed."
        else:
            update_firmware_path(args.flash)
            flash_firmware()
            sys.exit(0)
    #check
    if args.check == "local":
        get_uarm_version()
        sys.exit(0)
    elif args.check == "remote":
        print "Fetching the remote version..."
        get_latest_version()
        print "Latest firmware release version is: " + web_firmware_version
        sys.exit(0)

    #No Argument#####
    try:
        version_compare = comapre_version()
        print "Latest Firmware version: " + web_firmware_version
        print "Your uArm Firmware version: " + uarm_firmware_version
        if version_compare:
            print ("Would you want to upgrade your uArm with " + web_firmware_version +"?")
            user_choice = raw_input("Please Enter Y if yes. ")
            if user_choice == "Y" or user_choice == "y":
                download_firmware()
                flash_firmware()
            else:
                print "exit"
    except Exception:
        print "Latest Firmware version: " + web_firmware_version
        print ("Unknown uArm Firmware version, Would you want to upgrade your uArm with " + web_firmware_version +"?")
        user_choice = raw_input("Please Enter Y if yes. ")
        if user_choice == "Y" or user_choice == "y":
            download_firmware()
            flash_firmware()
        else:
            print "exit"

if __name__ == '__main__':
    main()
