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
from payloadcomputerdroneprojekt.mission_computer.filter import smooth

MISSION_PATH = "mission_file.json"
MISSION_PROGRESS = "__mission__.json"


class MissionComputer():
    def __init__(self, config: dict, port: str, camera: Camera,
                 communications=Communications, image_analysis=ImageAnalysis):
        self._comms = communications(port, config.get("communications", {}))
        error = None
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
                            level=logging.INFO)
        if error:
            logging.info(error)

        self._image = image_analysis(
            config=config.get("image", {}), camera=camera(
                config.get("camera", None)), comms=self._comms)
        # always starting camera for better performance
        self._image._camera.start_camera()
        self.config = config.get("mission_computer", {})

        self.setup()

    def setup(self):
        self.current_mission_plan = {}
        self.current_mission_plan.setdefault("parameter", {})
        self.progress = 0
        self.max_progress = -1
        self.running = False
        self.main_programm = None
        self.wait_plan = None
        self.actions = {
            "start_camera": self.start_camera,
            "stop_camera": self.stop_camera,
            "takeoff": self.takeoff,
            "land_at": self.land,
            "delay": self.delay,
            "list": self.execute_list,
            "mov_multiple": self.mov_multiple,
            "forever": self.forever,
            "mov": self.mov,
            "mov_to_objects_cap_pic": self.mov_to_objects_cap_pic,
        }
        self.none_counting_tasks = [
            "list", "mov_multiple"
        ]
        self.cancel_list = [
            self._image.stop_cam
        ]

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
            if os.path.exists(MISSION_PROGRESS):
                os.remove(MISSION_PROGRESS)

        if os.path.exists(MISSION_PATH):
            with open(MISSION_PATH, "r") as f:
                mission = json.load(f)
                rec_serialize(mission)
                self.current_mission_plan = mission
                self.current_mission_plan.setdefault("parameter", {})

        if not mission:
            self.progress = 0
            self.max_progress = -1
            if os.path.exists(MISSION_PROGRESS):
                os.remove(MISSION_PROGRESS)
            return

        if os.path.exists(MISSION_PROGRESS):
            with open(MISSION_PROGRESS, "r") as f:
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
            self._save_progress()
            await asyncio.sleep(0.1)

    def _save_progress(self):
        if self.running:
            obj = {
                "progress": self.progress,
                "max_progress": self.max_progress,
                "time": time.time()
            }
            with open(MISSION_PROGRESS, "w") as f:
                json.dump(obj, f)

    async def execute(self, action: dict):
        self.running = True
        a = action["action"]
        if a not in self.actions.keys():
            sp(f"Action not found {a} at exectuion"
               f" {self.progress} / {self.max_progress}")
            return
        try:
            await self.actions[a](action.get("commands", {}))
        except Exception as e:
            sp(f"Error in {a} ({self.progress} / {self.max_progress}): {e}")
        if a not in self.none_counting_tasks:
            self.progress += 1

        self._save_progress()
        self.running = False

    def start(self):
        asyncio.run(self._start())

    async def _start(self):
        await self._comms.connect()

        asyncio.create_task(self.save_progress())
        if len(self.current_mission_plan.keys()) > 0:
            self.running = True
            plan = self.current_mission_plan
            if self.progress > 0:
                plan = action_with_count(
                    self.current_mission_plan, self.progress)

            self.main_programm = asyncio.create_task(
                self.execute(plan))
        else:
            sp("No Valid Mision")
            sp("Waiting for Networking connection")
        self.wait_plan = asyncio.create_task(
            self._comms.receive_mission_file(self.new_mission))
        if self.main_programm:
            await self.main_programm
        if self.wait_plan:
            await self.wait_plan
        while True:
            asyncio.sleep(10)

    async def new_mission(self, plan: str):
        if self.main_programm:
            self.main_programm.cancel()
            for task in self.cancel_list:
                try:
                    task()
                except Exception as e:
                    sp(f"Error in canceling: {e}")
        self.running = False
        self.initiate(plan)
        self.start()

    async def start_camera(self, options: dict):
        sp("Starting Camera")
        self._image.start_cam(options.get("ips", 1))

    async def stop_camera(self, options: dict):
        sp("Stopping Camera")
        self._image.stop_cam()

    async def takeoff(self, options: dict):
        h = options.get(
            "height", self.current_mission_plan["parameter"].get(
                "flight_height", 5))
        sp(f"Taking Off to height {h}")
        await self._comms.start(h)

    async def land(self, objective: dict):
        sp(f"Landing at {objective['lat']:.2f} {objective['lon']:.2f}")
        await self.mov(options=objective)

        flight_height = self.current_mission_plan.get("parameter", {}).get(
            "flight_height", 10)
        await self.mov({
            "lat": objective["lat"],
            "lon": objective["lon"],
            "height": flight_height
        })
        if "color" not in objective.keys() or "type" not in objective.keys():
            sp("No color or type given")
            await self._comms.mov_by_vel(
                [0, 0, -self.config.get("land_speed", 2)])
            return

        sp(f"Suche Objekt vom Typ '{objective['type']}' mit Farbe '{objective[
            'color']}'")

        min_alt = 1
        detected_alt = await self._comms.get_relative_height()

        while detected_alt > min_alt:
            offset, detected_alt, yaw = \
                await self._image.get_current_offset_closest(
                    objective["color"], objective["type"])

            if offset is None:
                sp("Objekt nicht gefunden.")
                break

            vel = 1 / diag(offset[0], offset[1])
            if vel/2 > detected_alt:
                vel = detected_alt / 2

            await self._comms.mov_by_vel(
                smooth(offset[0], offset[1], vel), yaw)

            await asyncio.sleep(0.1)

        sp("Landeposition erreicht. Drohne landet.")
        await self._comms.mov_by_vel([0, 0, 0.5], 0)

    async def delay(self, options: dict):
        sp(f"Delay: {options.get('time', 1)}")
        await asyncio.sleep(options.get("time", 1))

    async def execute_list(self, options: list[dict]):
        for item in options:
            await self.execute(item)

    async def mov_multiple(self, options: list[dict]):
        sp(f"Moving Multiple {len(options)}")
        for item in options:
            await self.mov(item)
            self.progress += 1

    async def mov(self, options: dict):
        sp(f"Moving to {options['lat']:.2f} {options['lon']:.2f}")
        yaw = options.get("yaw")
        if "height" in options.keys():
            h = options["height"]
        else:
            h = self.current_mission_plan.get["parameter", {}].get("height", 5)
        pos = [options['lat'], options['lon'], h]
        if not await self._comms.is_flighing:
            await self._comms.start(h)
        await self._comms.mov_to_lat_lon_alt(pos, yaw)

    async def forever(self, options: dict):
        sp("Running Until Forever")
        while True:
            await asyncio.sleep(2)

    async def mov_to_objects_cap_pic(self, options: dict):
        sp("Moving to objects and taking picture")
        obj: list[dict] = self._image.get_filtered_objs()
        path = find_shortest_path(
            obj, await self._comms.get_position_lat_lon_alt())
        if "height" in options.keys():
            h = options["height"]
        else:
            h = self.current_mission_plan.get["parameter", {}].get("height", 5)

        for i, item in enumerate(path):
            sp(f"Moving to {i+1}/{len(path)}: {item}")
            await self.mov({"lat": item[0], "lon": item[1], "height": h})
            await asyncio.sleep(options.get("delay", 0.5))
            await self._image.take_image()


def find_shortest_path(objs: list[dict], start: list[float]):
    """
    find the shortest path to all objects
    """
    if len(objs) == 0:
        return []
    path = []
    for obj in objs:
        path.append(obj["pos"])
    path.sort(key=lambda x: abs(x[0] - start[0]) + abs(x[1] - start[1]))
    return path


def count_actions(actions):
    if actions["action"] == "list":
        c = 0
        for item in actions["commands"]:
            c += count_actions(item)
        return c
    elif actions["action"] == "mov_multiple":
        return len(actions["commands"])
    return 1


def action_with_count(plan, count: int):
    if plan["action"] == "list":
        for i, item in enumerate(plan["commands"]):
            ret = action_with_count(item, count)
            if not isinstance(ret, int):
                return {
                    "action": "list",
                    "commands": [ret] + plan["commands"][i+1:]
                }
            count = ret
    elif plan["action"] == "mov_multiple":
        if count < len(plan["commands"]):
            return {
                "action": "mov_multiple",
                "commands": plan["commands"][count:]
            }
        else:
            return count - len(plan["commands"])

    if count == 0:
        return plan
    return count - 1


def rec_serialize(obj):
    if isinstance(obj, dict):
        if "src" in obj.keys():
            if os.path.exists(obj["src"]):
                with open(obj["src"], "r") as f:
                    subobj = json.load(f)
                    obj["action"] = subobj["action"]
                    obj["commands"] = subobj["commands"]
                    rec_serialize(subobj["commands"])
            else:
                sp(f"File {obj['src']} not found")
    elif isinstance(obj, list):
        [rec_serialize(i) for i in obj]


def diag(x, y):
    return (x**2 + y**2)**0.5
