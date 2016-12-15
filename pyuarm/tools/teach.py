import time
from queue import Queue
from threading import Thread


class Teach:

    count = 0
    __queue = None
    __record_thread = None
    __play_thread = None

    def __init__(self, filepath, uarm):
        self.uarm = uarm
        self.filepath = filepath
        self.__record_flag = False
        self.__play_flag = False

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

    def start_play(self,speed=1):
        if not self.__play_flag:
            self.__play_flag = True
            self.__play_thread = Thread(target=self.__play, args=(speed,))
            self.__play_thread.start()

    def stop_play(self):
        print("Play Stop")
        self.__play_flag = False

    def get_progress(self):
        progress = self.__queue.get()
        self.__queue.task_done()
        return progress

    def wait_queue(self):
        self.__queue.join()

    def get_total_points(self):
        play_file = open(self.filepath, "r")
        lines = play_file.readlines()
        total = len(lines)
        play_file.close()
        return total

    def __record(self):
        self.__queue = Queue()
        record_file = open(self.filepath, 'w')
        self.uarm.set_servo_detach()
        self.uarm.set_report_position(0.02)
        count = 0
        while self.__record_flag:
            pos_array = self.uarm.get_report_position()
            record_file.write("mv,{},{},{},{}\n".format(pos_array[0], pos_array[1], pos_array[2], pos_array[3]))
            count += 1
            self.__queue.put(count)
        record_file.close()
        self.uarm.close_report_position()
        self.uarm.set_servo_attach()
        self.__record_flag = False
        self.__queue.join()
        print("Record Stop")

    def __play(self, speed=1):
        self.__queue = Queue()
        if speed != 0:
            delay_time = 0.02 / speed
        else:
            delay_time = 0
        play_file = open(self.filepath, "r")
        lines = play_file.readlines()
        total = len(lines)
        count = 0
        last_progress = 0
        # start_time = time.time()
        while self.__play_flag and len(lines) > 0:
            line = lines.pop()
            count += 1
            values = line.split(',')
            self.uarm.set_position(float(values[1]), float(values[2]), float(values[3]), speed=0, wait=False)
            time.sleep(delay_time)
            progress = int(count / total * 100)
            if progress - last_progress == 1:
                # print ("Progress: {}%".format(progress))
                self.__queue.put(progress)
                last_progress = progress
        # print ("End Time: {}".format(time.time() - start_time))
        # time.sleep(0.1)
        self.stop_play()
        time.sleep(0.1)
        self.__queue.join()
        play_file.close()

