import asyncio.selector_events
from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
from payloadcomputerdroneprojekt.camera import Camera
import os
import logging
import time
import json
import shutil
from payloadcomputerdroneprojekt.helper import smart_print as sp
import asyncio

MISSION_PATH = "mission_file.json"
MISSION_PROGRESS = "__mission__.json"


class MissionComputer():
    def __init__(self, config: dict, port: str, camera: Camera,
                 communications=Communications, image_analysis=ImageAnalysis):
        self._comms = communications(port, config.get("communications", {}))
        try:
            path = config.get("mission_storage", "mission_storage")
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            error = e
            print(
                "Working directory not accesable, "
                "switching to 'mission_storage'")
            path = "mission_storage"
        os.chdir(path)
        logging.basicConfig(filename="flight.log",
                            format='%(asctime)s %(message)s',
                            filemode='w')
        if error:
            logging.info(error)

        self._image = image_analysis(
            config=config.get("image", {}), camera=camera(
                config.get("camera", None)), comms=self._comms)
        self.config = config

        self.current_mission_plan = {}
        self.progress = 0
        self.max_progress = -1
        self.running = False
        self.main_programm = None

        asyncio.create_task(self.save_progress())

    def initiate(self, missionfile=""):
        """
        this function starts the computer

        see "Ablaufdiagramm.png"

        parms:
         missionfile: file descriping the mission and it's parameters
                      if not given waiting for Network
        """
        mission: dict = None
        if os.path.exists(missionfile):
            shutil.copyfile(missionfile, MISSION_PATH)
            try:
                os.remove(MISSION_PROGRESS)
            except Exception:
                pass

        if os.path.exists(MISSION_PATH):
            with open(missionfile, "r") as f:
                mission = json.load(f)
                self.current_mission_plan = mission

        if not mission:
            self.progress = 0
            self.max_progress = -1
            try:
                os.remove(MISSION_PROGRESS)
            except Exception:
                pass
            return

        if os.path.exists(MISSION_PROGRESS):
            with open(missionfile, "r") as f:
                progress = json.load(f)

            if abs(progress["time"] - time.time()
                   ) < self.config.get("recouver_time", 10):
                if count_actions(mission) == progress["max_progress"]:
                    self.progress = progress["progress"]
                    self.max_progress = progress["max_progress"]
                    return

        self.progress = mission.get("progress", 0)
        self.max_progress = count_actions(mission)

    async def save_progress(self):
        while True:
            if self.running:
                obj = {
                    "progress": self.progress,
                    "max_progress": self.max_progress,
                    "time": time.time()
                }
                with open(MISSION_PROGRESS) as f:
                    json.dump(obj, f)
            await asyncio.sleep(0.5)

    async def execute(self, action: dict):
        a = action["mission_type"]

        def fb(_):
            sp(f"Action not found {a} at exectuion"
               f" {self.progress} / {self.max_progress}")
        await self.actions.get([a], fb)(action["commands"])

    def start(self):
        if len(dict.keys()) > 0:
            self.running = True
            if self.progress == 0:
                self.main_programm = asyncio.create_task(
                    self.execute(self.current_mission_plan))
            else:
                self.main_programm = asyncio.create_task(
                    self.execute(action_with_count(
                        self.current_mission_plan, self.progress)))
        else:
            sp("No Valid Mision")
            sp("Waiting for Networking connection")
            asyncio.run(self._comms.receive_mission_file(self.new_mission))

    async def new_mission(self, plan: str):
        if self.main_programm:
            self.main_programm.cancel()
        self.running = False
        self.initiate(plan)
        asyncio.create_task(self._comms.receive_mission_file(self.new_mission))
        self.start()

    @getattr
    def actions(self) -> dict:
        return {
            "start_camera": self.start_camera,
            "stop_camera": self.stop_camera,
            "takeoff": self.takeoff,
            "land_at": self.land,
            "delay": self.delay,
            "list": self.execute_list,
            "mov_multiple": self.mov_multiple,
            "forever": self.forever,
            "mov": self.mov
        }

    async def start_camera(self, options: dict):
        pass

    async def stop_camera(self, options: dict):
        pass

    async def takeoff(self, options: dict):
        pass

    async def land(self, options: dict):
        pass

    async def delay(self, options: dict):
        await asyncio.sleep(options.get())

    async def execute_list(self, options: list[dict]):
        for item in options:
            await self.execute(item)

    async def mov_multiple(self, options: list[dict]):
        sp(f"Moving Multiple {len(options)}")
        for item in options:
            await self.mov(item)

    async def mov(self, options: dict):
        sp(f"Moving to {options['lat']:.2f} {options['lon']:.2f}")
        yaw = options.get("yaw")
        if "height" in options.keys():
            h = options["height"]
        else:
            h = self.current_mission_plan.get["parameter", {}].get("height", 5)
        pos = [options['lat'], options['lon'], h]
        self._comms.mov_to_lat_lon_alt(pos, yaw)

    async def forever(self, options: dict):
        sp("Running Until Forever")
        while True:
            await asyncio.sleep(2)


def count_actions(actions):
    if actions["mission_type"] == "list":
        c = 0
        for item in actions["commands"]:
            c += count_actions(item)
        return c
    elif actions["mission_type"] == "mov_multiple":
        return len(actions["commands"])
    return 1


def action_with_count(plan, count: int) -> any[int, dict]:
    if plan["mission_type"] == "list":
        for i, item in enumerate(plan["commands"]):
            ret = action_with_count(item, count)
            if not isinstance(ret, int):
                return {
                    "mission_type": "list",
                    "commands": [ret] + plan["commands"][i+1:]
                }
            count = ret
    elif plan["mission_type"] == "mov_multiple":
        if count < len(plan["commands"]):
            return {
                "mission_type": "mov_multiple",
                "commands": plan["commands"][count:]
            }
        else:
            return count - len(plan["commands"])

    if count == 1:
        return plan
    return count - 1
