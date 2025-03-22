from drone_sitl import DroneSITL
import tempfile
import time


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
            msg = self.drone.connection.recv_match(
                type="GLOBAL_POSITION_INT", blocking=True)
            print(msg)
            time.sleep(self.rate)


if __name__ == "__main__":
    programm = LogWriter()
    programm.setup()
    programm.run()
