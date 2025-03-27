import drone_raspi


class MissionComputer(drone_raspi.Drone):
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    drone = MissionComputer()
    drone.setup()
    print("Setup Complete")
    drone.run()
