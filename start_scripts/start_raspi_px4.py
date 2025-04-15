from payloadcomputerdroneprojekt.mission_computer import MissionComputer
from payloadcomputerdroneprojekt.camera.raspi2 import Camera


def main():
    camera = Camera()
    port = "serial:///dev/ttyAMA0:57600"
    computer = MissionComputer(camera=camera, port=port)
    computer.setup()
    computer.start()


if __name__ == "__main__":
    main()
