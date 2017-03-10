import os
from os.path import expanduser
import io
import json
from . import PY3
from .log import printf
if PY3:
    import urllib.request as req
else:
    import urllib2 as req

# ################################### Config ################################
home_dir = os.path.join(expanduser("~"), "uarm", "")
if not os.path.exists(home_dir):
    os.mkdir(home_dir)
ua_dir = os.path.join(home_dir, "assistant")
if not os.path.exists(ua_dir):
    os.mkdir(ua_dir)

config_file = os.path.join(ua_dir, "config.json")
default_config = {
    "branch": "dev",
    "firmware_filename": "firmware.hex",
    "bluetooth_filename": "bluetooth.hex",
    "hardware_id": "USB VID:PID=0403:6001",
    "calibration_filename": "calibration.hex",
    "calibration_url": "http://download.ufactory.cc/firmware/pro/calibration.hex",
    "firmware_url": "http://download.ufactory.cc/firmware/dev/firmware.hex",
    "driver_url": "http://download.ufactory.cc/driver/ftdi_win.zip",
    "bluetooth_url": "http://download.ufactory.cc/firmware/pro/bluetooth.hex",
    "latest_version": "",
}


def load_config():
    try:
        if not os.path.exists(config_file):
            save_default_config()
        with io.open(config_file, "r", encoding="utf-8") as data_file:
            settings = json.load(data_file)
        return settings
    except Exception as e:
        printf("Error occurred when reading settings. {}".format(e))
        return default_config


def save_config(settings):
    cf = open(config_file, "w")
    json.dump(settings, open(config_file, 'w'),
              sort_keys=False, indent=4)
    cf.close()


def save_default_config():
    json.dump(default_config, open(config_file, 'w'),
              sort_keys=False, indent=4, separators=(',', ': '))
    settings = default_config
    save_config(settings)


# ############## online config file #################
def get_online_config():
    online_config_url = "http://download.ufactory.cc/version.json"
    response = req.urlopen(online_config_url)
    online_config_data = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))
    return online_config_data
