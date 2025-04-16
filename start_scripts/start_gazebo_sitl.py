from payloadcomputerdroneprojekt.mission_computer import MissionComputer
from payloadcomputerdroneprojekt.camera.gazebo_sitl import GazeboCamera


def main():
    camera = GazeboCamera()
    port = "udp://:14540"
    computer = MissionComputer(camera=camera, port=port)
    computer.setup()
    computer.start()


if __name__ == "__main__":
    main()
