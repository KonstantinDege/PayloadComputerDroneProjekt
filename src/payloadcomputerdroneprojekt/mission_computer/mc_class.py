from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
from payloadcomputerdroneprojekt.camera import AbstractCamera
from payloadcomputerdroneprojekt.mission_computer.helper \
    import rec_serialize, count_actions, action_with_count, diag, \
    find_shortest_path
import os
import logging
import time
import json
import shutil
from payloadcomputerdroneprojekt.helper import smart_print as sp
import asyncio
from typing import Any, Callable, Dict, List, Optional


MISSION_PATH = "mission_file.json"
MISSION_PROGRESS = "__mission__.json"


def test_rem(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


class MissionComputer:
    """
    MissionComputer class for managing drone missions, communication, and image
    analysis.

    This class handles mission initialization, execution, progress tracking,
    and communication with the drone and its subsystems.

    :param config: Configuration dictionary for the mission computer and
        subsystems.
    :type config: dict
    :param port: Communication port for the drone.
    :type port: str
    :param camera: Camera class to be used for image analysis.
    :type camera: type[AbstractCamera]
    :param communications: Communications class for drone communication.
    :type communications: type[Communications], optional
    :param image_analysis: ImageAnalysis class for image processing.
    :type image_analysis: type[ImageAnalysis], optional
    """

    def __init__(
        self,
        config: dict,
        port: str,
        camera: type[AbstractCamera],
        communications: type[Communications] = Communications,
        image_analysis: type[ImageAnalysis] = ImageAnalysis
    ) -> None:
        """
        Initialize the MissionComputer instance.

        Sets up communication, image analysis, logging, and working directory.

        :param config: Configuration dictionary.
        :type config: dict
        :param port: Communication port.
        :type port: str
        :param camera: Camera class.
        :type camera: type[AbstractCamera]
        :param communications: Communications class.
        :type communications: type[Communications], optional
        :param image_analysis: ImageAnalysis class.
        :type image_analysis: type[ImageAnalysis], optional
        """
        self.set_work_dir(config)
        logging.basicConfig(filename="flight.log",
                            format='%(asctime)s %(message)s',
                            level=logging.INFO)

        self._comms: Communications = communications(
            port, config.get("communications", {}))

        self._image: ImageAnalysis = image_analysis(
            config=config.get("image", {}), camera=camera(
                config.get("camera", None)), comms=self._comms)

        self._image._camera.start_camera()
        self.config: dict = config.get("mission_computer", {})

        self._setup()

    def set_work_dir(self, config: dict) -> None:
        error: Optional[Exception] = None
        try:
            path: str = config.get("mission_storage", "mission_storage")
            print(path)
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            error = e
            print(
                "Working directory not accesable, "
                "switching to 'mission_storage'")
            path = "mission_storage"
            os.makedirs(path, exist_ok=True)
        os.chdir(path)
        if error:
            logging.info(str(error))

    def _setup(self) -> None:
        """
        Internal setup for mission plan, progress, and available actions.
        """
        self.task = None
        self._old_task = None
        self.current_mission_plan: dict = {}
        self.current_mission_plan.setdefault("parameter", {})
        self.progress: int = 0
        self.max_progress: int = -1
        self.running: bool = False
        self.main_programm: Optional[asyncio.Task] = None
        self.actions: Dict[str, Callable] = {
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
        self.none_counting_tasks: List[str] = [
            "list", "mov_multiple"
        ]
        self.cancel_list: List[Callable] = [
            self._image.stop_cam
        ]
        # TODO: add on off state filter camera is
        # not being reactivated on restart

    def initiate(self, missionfile: str = "") -> None:
        """
        Initialize or reset the mission plan from a file.

        :param missionfile: Path to the mission file.
        :type missionfile: str, optional
        """
        if os.path.exists(MISSION_PROGRESS):
            try:
                with open(MISSION_PROGRESS, "r") as f:
                    progress = json.load(f)
            # Check if the mission can be recovered based on time
                if abs(progress["time"] - time.time()
                       ) > self.config.get("recouver_time", 10):
                    test_rem(MISSION_PROGRESS)
                    test_rem(MISSION_PATH)
            except Exception:
                sp("Error reading progress file, resetting progress")
                test_rem(MISSION_PROGRESS)
                test_rem(MISSION_PATH)
                return

        mission: Optional[dict] = None
        if os.path.exists(missionfile):
            shutil.copyfile(missionfile, MISSION_PATH)
            test_rem(MISSION_PROGRESS)

        if os.path.exists(MISSION_PATH):
            with open(MISSION_PATH, "r") as f:
                mission = json.load(f)
                rec_serialize(mission)
                self.current_mission_plan = mission
                self.current_mission_plan.setdefault("parameter", {})

        if mission is None:
            self.progress = 0
            self.max_progress = -1
            test_rem(MISSION_PROGRESS)
            return
        try:
            if os.path.exists(MISSION_PROGRESS):
                with open(MISSION_PROGRESS, "r") as f:
                    progress = json.load(f)
                if count_actions(mission) == progress["max_progress"]:
                    self.progress = progress["progress"]
                    self.max_progress = progress["max_progress"]
                    return
        except Exception:
            sp("Error reading progress file, resetting progress")
            test_rem(MISSION_PROGRESS)
            self.progress = 0
            self.max_progress = -1
            return

        self.progress = mission.get("progress", 0)
        self.max_progress = count_actions(mission)

    async def save_progress(self) -> None:
        """
        Periodically save the current mission progress to a file.
        """
        while True:
            self._save_progress()
            await asyncio.sleep(0.1)

    def _save_progress(self) -> None:
        """
        Save the current progress to the progress file if the mission is
        running.
        """
        if self.running:
            obj = {
                "progress": self.progress,
                "max_progress": self.max_progress,
                "time": time.time()
            }
            with open(MISSION_PROGRESS, "w") as f:
                json.dump(obj, f)

    async def execute(self, action: dict) -> None:
        """
        Execute a single mission action.

        :param action: Action dictionary containing the action type and
            commands.
        :type action: dict
        """
        self.running = True
        a: str = action["action"]

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
        if self.progress >= self.max_progress:
            await self.status("Mission Completed")
            self.running = False
            if os.path.exists(MISSION_PROGRESS):
                os.remove(MISSION_PROGRESS)
            if os.path.exists(MISSION_PATH):
                os.remove(MISSION_PATH)

    def start(self) -> None:
        """
        Start the mission computer's main event loop.
        """
        self.task = self._start
        asyncio.run(self._task())

    async def _task(self) -> None:
        while True:
            if self.task is not None:
                if self._old_task is not None:
                    self._old_task.cancel()
                self._old_task = asyncio.create_task(self.task())
                self.task = None
            await asyncio.sleep(0.1)

    async def _start(self) -> None:
        """
        Asynchronous main loop for mission execution and communication.
        """
        await self._comms.connect()
        await self.status("Mission Computer Started")

        asyncio.create_task(self.save_progress())
        await self.status(f"Starting with Progress: {self.progress}")
        if "action" in self.current_mission_plan.keys():
            self.running = True
            plan: dict = self.current_mission_plan
            if self.progress > 0:
                plan = action_with_count(
                    self.current_mission_plan, self.progress)
                if isinstance(plan, int):
                    sp(f"Progress {self.progress} exceeds plan actions, "
                       f"resetting to 0")
                    self.progress = 0
                    plan = self.current_mission_plan
            if self.main_programm is not None:
                self.main_programm.cancel()
            self.main_programm = asyncio.create_task(
                self.execute(plan))
        else:
            await self.status("No Valid Mision")
            sp("Waiting for Networking connection")

    async def new_mission(self, plan: str) -> None:
        """
        Callback for receiving a new mission plan.

        :param plan: Path to the new mission plan file.
        :type plan: str
        """
        if self.main_programm:
            try:
                self.main_programm.cancel()
            except asyncio.CancelledError:
                sp("Main programm already canceled")
            for task in self.cancel_list:
                try:
                    task()
                except Exception as e:
                    sp(f"Error in canceling: {e}")
        self.running = False
        self.initiate(plan)
        self.task = self._start

    async def start_camera(self, options: dict) -> None:
        """
        Start the camera subsystem.

        :param options: Options for starting the camera (e.g., images per
            second).
        :type options: dict
        """
        await self.status("Starting Camera")
        self._image.start_cam(options.get("ips", 1))

    async def stop_camera(self, options: dict) -> None:
        """
        Stop the camera subsystem and process filtered objects.

        :param options: Options for stopping the camera.
        :type options: dict
        """
        await self.status("Stopping Camera")
        self._image.stop_cam()
        self._image.get_filtered_objs()

    async def takeoff(self, options: dict) -> None:
        """
        Command the drone to take off to a specified height.

        :param options: Options containing the target height.
        :type options: dict
        """
        h: float = options.get(
            "height", self.current_mission_plan["parameter"].get(
                "flight_height", 5))
        await self.status(f"Taking Off to height {h}")
        await self._comms.start(h)

    async def land(self, objective: dict) -> None:
        """
        Land the drone at a specified location, optionally using color/shape
        detection.

        :param objective: Dictionary with landing coordinates and optional
            color/shape.
        :type objective: dict
        """
        if "lat" not in objective.keys() or "lon" not in objective.keys():
            await self.status(
                "No landing position given, landing at current position")
            await self._comms.mov_by_vel(
                [0, 0, self.config.get("land_speed", 2)])
            await self._comms.landed()
            return

        sp(f"Landing at {objective['lat']:.6f} {objective['lon']:.6f}")
        if not (await self._comms.is_flying()):
            return
        await self.mov(options=objective)

        if "color" not in objective.keys():
            sp("No color given")
            await self._comms.mov_by_vel(
                [0, 0, self.config.get("land_speed", 2)])
            return

        sp(f"Suche Objekt vom Typ '{objective.get('shape', None)}' "
           f"mit Farbe '{objective['color']}'")

        min_alt: float = 1
        detected_alt: float = await self._comms.get_relative_height()

        # Loop to adjust position until the drone is close enough to the object
        while detected_alt > min_alt:
            offset, detected_alt, yaw = \
                await self._image.get_current_offset_closest(
                    objective["color"], objective.get('shape', None))

            if offset is None:
                await self.status("Objekt nicht gefunden.")
                break

            vel_ver: float = 1 / diag(offset[0], offset[1])
            if vel_ver/2 > detected_alt:
                vel_ver = detected_alt / 2
            await self._comms.mov_by_vel(
                [offset[0]/10, offset[1]/10, vel_ver], yaw)

            await asyncio.sleep(0.1)

        await self.status("Landeposition erreicht. Drohne landet.")
        await self._comms.mov_by_vel(
            [0, 0, self.config.get("land_speed", 2)])
        await self._comms.landed()

    async def delay(self, options: dict) -> None:
        """
        Delay execution for a specified amount of time.

        :param options: Dictionary with the delay time in seconds.
        :type options: dict
        """
        sp(f"Delay: {options.get('time', 1)}")
        await asyncio.sleep(options.get("time", 1))

    async def execute_list(self, options: List[dict]) -> None:
        """
        Execute a list of actions sequentially.

        :param options: List of action dictionaries.
        :type options: List[dict]
        """
        for item in options:
            await self.execute(item)

    async def mov_multiple(self, options: List[dict]) -> None:
        """
        Move to multiple locations sequentially.

        :param options: List of movement command dictionaries.
        :type options: List[dict]
        """
        await self.status(f"Moving Multiple {len(options)}")
        for item in options:
            await self.mov(item)
            self.progress += 1

    async def mov(self, options: dict) -> None:
        """
        Moves the drone to the specified latitude, longitude, and height, with an optional yaw.
        
        If height is not provided in options, uses the mission plan's default flight height or 5 meters.
        """
        yaw: Optional[float] = options.get("yaw")
        if "height" in options.keys():
            h: float = options["height"]
        else:
            h: float = self.current_mission_plan.get(
                "parameter", {}).get("flight_height", 5)
        await self.status(
            f"Moving to {options['lat']:.6f} {options['lon']:.6f} "
            f"{h:.2} {yaw}")

        pos: List[float] = [options['lat'], options['lon'], h]
        if not await self._comms.is_flying():
            await self._comms.start(h)

        await self._comms.mov_to_lat_lon_alt(pos, yaw)

    async def forever(self, options: dict) -> None:
        """
        Run an infinite loop (used for testing or waiting).

        :param options: Options dictionary (unused).
        :type options: dict
        """
        sp("Running Until Forever")
        while True:
            await asyncio.sleep(2)

    async def mov_to_objects_cap_pic(self, options: dict) -> None:
        """
        Move to detected objects and capture images at each location.

        :param options: Dictionary with movement and delay options.
        :type options: dict
        """
        sp("Moving to objects and taking picture")
        obj: List[dict] = self._image.get_filtered_objs()
        path: List[Any] = find_shortest_path(
            obj, await self._comms.get_position_lat_lon_alt())
        if "height" in options.keys():
            h: float = options["height"]
        else:
            h: float = self.current_mission_plan.get(
                "parameter", {}).get("height", 5)

        for i, item in enumerate(path):
            sp(f"Moving to {i+1}/{len(path)}: {item}")
            await self.mov({"lat": item[0], "lon": item[1], "height": h})
            await asyncio.sleep(options.get("delay", 0.5))
            await self._image.take_image()

    async def status(self, msg: str) -> None:
        """
        Send a status message to the communication subsystem.

        :param msg: Status message to send.
        :type msg: str
        """
        sp(msg)
        await self._comms.send_status(msg)
