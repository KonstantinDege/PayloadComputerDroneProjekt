from payloadcomputerdroneprojekt.mission_computer import MissionComputer
from payloadcomputerdroneprojekt.camera.raspi2 import RaspiCamera


def main():
    camera = RaspiCamera()
    port = "serial:///dev/ttyAMA0:57600"
    computer = MissionComputer(camera=camera, port=port)
    computer.setup()
    computer.start()


if __name__ == "__main__":
    main()
