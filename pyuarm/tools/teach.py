import time
from .. import PY3
if PY3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty
from threading import Thread
from ..protocol import BUTTON_MENU, BUTTON_PLAY
import os


class Teach:

    count = 0
    __queue = None
    __record_thread = None
    __play_thread = None

    def __init__(self, file_path, uarm):
        self.uarm = uarm
        self.file_path = file_path
        self.__record_flag = False
        self.__play_flag = False
        self.__ready = False
        self.__ready_thread = None
        self.__speed = 1

    def set_speed(self, speed=1):
        self.__speed = speed

    def get_speed(self):
        return self.__speed

    def is_standby_mode(self):
        return self.__ready

    def start_standby_mode(self):
        # This Mode will listen Menu Button & Play Button
        self.__ready = True
        if self.uarm.is_connected():
            self.uarm.set_report_button()
        self.__ready_thread = Thread(target=self.__checking_button)
        self.__ready_thread.start()

    def stop_standby_mode(self):
        self.__ready = False

    def __checking_button(self):
        while self.__ready:
            if not self.__record_flag and not self.__play_flag:
                menu_button = self.uarm.get_report_button(BUTTON_MENU, wait=False)
                play_button = self.uarm.get_report_button(BUTTON_PLAY, wait=False)
                if menu_button is not None:
                    self.start_record()
                elif play_button is not None:
                    self.start_play()
            time.sleep(0.01)

    def is_recording(self):
        return self.__record_flag

    def is_playing(self):
        return self.__play_flag

    def start_record(self):
        if not self.__record_flag:
            self.__record_flag = True
            self.__record_thread = Thread(target=self.__record)
            self.__record_thread.start()

    def stop_record(self):
        self.__record_flag = False

    def start_play(self, speed=1):
        if not self.__play_flag:
            self.__play_flag = True
            self.__play_thread = Thread(target=self.__play, args=(speed,))
            self.__play_thread.start()

    def stop_play(self):
        self.__play_flag = False

    def get_progress(self, wait=True):
        try:
            progress = self.__queue.get(block=wait)
            self.__queue.task_done()
            return progress
        except Empty:
            return None

    def wait_queue(self):
        self.__queue.join()

    def get_total_points(self):
        play_file = open(self.file_path, "r")
        lines = play_file.readlines()
        total = len(lines)
        play_file.close()
        return total

    def __record(self):
        record_file = open(self.file_path, 'w')
        self.__queue = Queue()
        self.uarm.set_servo_detach()
        self.uarm.set_report_position(0.05)
        self.uarm.set_report_button()
        pump_on = False
        count = 0
        start_time = time.time()
        while self.__record_flag:
            if self.__ready:
                menu_button = self.uarm.get_report_button(BUTTON_MENU, wait=False)
                if menu_button is not None:
                    break
            pos_array = self.uarm.get_report_position()
            play_button = self.uarm.get_report_button(BUTTON_PLAY, wait=False)
            if play_button is not None:
                pump_on = not pump_on
                self.uarm.set_pump(pump_on)
                record_file.write("ee,{}\n".format(1 if pump_on else 0))
            record_file.write("mv,{},{},{},{}\n".format(pos_array[0], pos_array[1], pos_array[2], pos_array[3]))
            count += 1
            self.__queue.put(count)
        print("Record Time: {}".format(time.time() - start_time))
        record_file.close()
        self.uarm.close_report_position()
        self.uarm.reset()
        self.__record_flag = False
        # self.__queue.join()
        # print("Record Stop")

    def __play(self, speed=None):
        if not os.path.exists(self.file_path):
            return None
        if speed is None:
            speed = self.__speed
        play_file = open(self.file_path, "r")
        self.__queue = Queue()
        if speed > 2:
            speed = 2
        elif speed <= 0.5:
            speed = 0.25
        delay_time = 0.025 / speed
        print ("delay_time: {}".format(delay_time))
        lines = play_file.readlines()
        total = len(lines)
        print ("file_path is {}, total is : {}".format(self.file_path, total))
        count = 0
        last_progress = 0
        start_time = time.time()
        while self.__play_flag and len(lines) > 0:
            if self.__ready:
                play_button = self.uarm.get_report_button(BUTTON_PLAY, wait=False)
                if play_button is not None:
                    break
            line = lines.pop(0)
            count += 1
            values = line.split(',')
            if values[0].startswith("mv"):
                self.uarm.set_position(float(values[1]), float(values[2]), float(values[3]), speed=0, wait=False)
            else:
                self.uarm.set_pump(int(values[1]) == 1, wait=False)
            time.sleep(delay_time)
            progress = int(count / total * 100)
            if progress - last_progress == 1:
                # print ("Progress: {}%".format(progress))
                self.__queue.put(progress)
                last_progress = progress
        print ("Play Time: {}".format(time.time() - start_time))
        self.stop_play()
        # self.uarm.reset()
        time.sleep(0.1)
        play_file.close()
        print("Stop")
