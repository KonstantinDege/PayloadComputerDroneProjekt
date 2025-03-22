from payloadcomputerdroneprojekt.drone_sitl import DroneSITL
import tempfile
import time
from os.path import join
import cv2
import os

class LogWriter:
    def __init__(self, dir=None, rate=5):
        self.rate = rate
        self.drone = DroneSITL()
        if not dir:
            dir = tempfile.mkdtemp("pics")
        self.dir = dir
        print(f"output directory: {dir}")

    def setup(self):
        self.drone.setup()

    def run(self):

        while True:
            msg = self.drone.connection_mavlink.recv_match(
                type="GLOBAL_POSITION_INT", blocking=True)
            print(msg)
            t = time.time()
            frame = self.drone.get_current_frame()
            dir = join(self.dir,str(int(t)))
            os.mkdir(dir)
            with open(join(dir, 'coords.txt'), "w+") as f:
                f.write(str(msg))
            cv2.imwrite(join(dir, 'frame.jpg'), frame)
            time.sleep(self.rate)


if __name__ == "__main__":
    programm = LogWriter()
    programm.setup()
    programm.run()
