from payloadcomputerdroneprojekt import MissionComputer
from payloadcomputerdroneprojekt.camera import RaspiCamera
import os
import json

mission = r"C:\Users\User\Desktop\6_Semester-Drone\PayloadComputerDroneProjekt\configs\mission1.json"
config = r"C:\Users\User\Desktop\6_Semester-Drone\PayloadComputerDroneProjekt\start_scripts\config_px4.json"


mission = os.path.abspath(mission)
with open(config) as f:
    config = json.load(f)
port = "serial:///dev/ttyAMA0:115200"
computer = MissionComputer(config=config, camera=RaspiCamera, port=port)
computer.initiate(mission)
computer.start()
