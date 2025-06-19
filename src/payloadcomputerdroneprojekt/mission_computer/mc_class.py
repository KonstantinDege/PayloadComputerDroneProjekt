from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
from payloadcomputerdroneprojekt.camera import AbstractCamera
from payloadcomputerdroneprojekt.mission_computer.scan_planer import \
    plan_scan, export_geojson
from payloadcomputerdroneprojekt.mission_computer.helper \
    import rec_serialize, count_actions, action_with_count, diag, \
    find_shortest_path, PIDController
import os
import logging
import time
import json
import shutil
from payloadcomputerdroneprojekt.helper import smart_print as sp
import asyncio
from typing import Any, Callable, Dict, List, Optional
import numpy as np

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
            "mov_local": self.mov_local,
            "scan_area": self.scan_area,
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
        else:
            test_rem(MISSION_PROGRESS)
            test_rem(MISSION_PATH)

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
        asyncio.create_task(self.save_progress())
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
        if not await self._comms.is_flying():
            return

        if "lat" in objective and "lon" in objective:
            sp(f"Landing at {objective['lat']:.6f} {objective['lon']:.6f}")
            await self.mov(options=objective)
        else:
            await self.status("No lat/lon given – skipping GPS movement")

        try:
            await self.smart_land(objective)
        except Exception as e:
            sp(f"Error during smart land: {e}")
            await self.status("Smart land failed, landing at current position")

        await self.status("Landeposition erreicht. Drohne landet.")
        await self._comms.mov_by_vel(
            [0, 0, self.config.get("land_speed", 2)])
        await self._comms.landed()

    async def smart_land(self, objective: dict) -> None:
        yaw_pid = PIDController(
            Kp=0.25, Ki=0.0, Kd=0.1, output_limits=(-15, 15))

        if "color" not in objective.keys():
            sp("No color given")
            return

        sp(f"Suche Objekt vom Typ '{objective.get('shape', None)}' "
           f"mit Farbe '{objective['color']}'")

        min_alt: float = self.current_mission_plan.get(
            "parameter", {}).get("decision_height", 1)

        if self.config.get("indoor", False):
            detected_alt: float = -1*(await self._comms.get_position_xyz())[2]
        else:
            detected_alt: float = await self._comms.get_relative_height()

        if detected_alt <= 0:
            sp(f"Warning: detected_alt below 0 ({detected_alt:.2f}),"
               " clamping to 0")
            detected_alt = 0.001

        tries = 5
        old_time = time.time()
        old_d = 0.0
        while detected_alt > min_alt:
            old_alt = detected_alt
            offset, detected_alt, yaw = \
                await self._image.get_current_offset_closest(
                    objective["color"], objective.get('shape', None),
                    indoor=self.config.get("indoor", False))

            if offset is None:
                await self.status("Objekt nicht gefunden.")
                tries -= 1
                detected_alt = old_alt
                if tries <= 0:
                    sp("Max tries reached, aborting landing")
                    return
                sp("skip to next")
                continue

            tries = 5

            sp(f"Offset: {offset}, Detected Altitude: {detected_alt}, "
               f"Yaw: {yaw}")

            d = diag(offset[0], offset[1])
            vel_ver: float = 0.002 / d
            if vel_ver*2 > detected_alt:
                vel_ver = detected_alt / 2
            if abs(d-old_d) > 0.25:
                vel_ver = 0
            sp(f"Vertical Velocity: {vel_ver:.2f}")

            def smart_xy(x):
                return np.tanh(x) / 2

            now = time.time()
            dt = now - old_time
            old_time = now

            # PID control for x, y, z, and yaw
            vx = smart_xy(offset[0])
            vy = smart_xy(offset[1])
            vyaw = yaw_pid(np.tanh(-yaw/15)*15, dt)

            sp(f"PID vx: {vx:.2f}, vy: {vy:.2f}, vyaw: {vyaw:.2f}")

            await self._comms.mov_by_vel([vx, vy, vel_ver], vyaw)

            old_d = d

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
        Move the drone to a specified latitude, longitude, and height.

        :param options: Dictionary with 'lat', 'lon', and optional 'height' and
            'yaw'.
        :type options: dict
        """
        yaw: Optional[float] = options.get("yaw")
        if "height" in options.keys():
            h: float = options["height"]
        else:
            h: float = self.current_mission_plan.get(
                "parameter", {}).get("flight_height", 5)
        await self.status(
            f"Moving to {options['lat']:.6f} {options['lon']:.6f} "
            f"{h:.2f} {yaw}")

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

    async def mov_local(self, options: dict) -> None:
        """
        Move the drone to a specified local position (x, y, z) in meters.

        :param options: Dictionary with 'x', 'y', and optional 'z' and 'yaw'.
            x: forward (North), y: right (East), z: down (positive)
        :type options: dict
        """
        if "x" in options and "y" in options:
            await self._move_local(options)
        elif "dx" in options and "dy" in options:
            await self._move_local_delta(options)
        else:
            await self.status("No valid input fields in local move")

    async def _move_local(self, options: dict) -> None:
        """
        Move the drone to a specified local position (x, y, z) in meters.

        :param options: Dictionary with 'x', 'y', and optional 'z' and 'yaw'.
            x: forward (North), y: right (East), z: down (positive)
        :type options: dict
        """

        # Extract coordinates
        x, y = options['x'], options['y']

        if "z" in options.keys():
            z: float = options["z"]
        else:
            z: float = -1 * self.current_mission_plan.get(
                "parameter", {}).get("height", 1)

        yaw: Optional[float] = options.get("yaw")

        await self.status(
            f"Moving to local x={x:.2f}, y={y:.2f}, z={z:.2f}")

        pos_local: List[float] = [x, y, z]

        if not await self._comms.is_flying():
            # Use negative z for takeoff height since NED z is positive
            # downward
            await self._comms.start(abs(z))

        await self._comms.mov_to_xyz(pos_local, yaw)

    async def _move_local_delta(self, options: dict) -> None:
        """
        Move the drone by a specified delta in local coordinates (dx, dy, dz).

        :param options: Dictionary with 'dx', 'dy', and optional 'dz' and
            'yaw'.
        :type options: dict
        """

        dx, dy = options['dx'], options['dy']
        dz: float = options.get("dz", 0)

        yaw: Optional[float] = options.get("yaw", 0)

        await self.status(
            f"Moving local delta dx={dx:.2f}, dy={dy:.2f}, dz={dz:.2f}")

        pos_local: List[float] = [dx, dy, dz]

        if not await self._comms.is_flying():
            # Use negative dz for takeoff height since NED z is positive
            # downward
            z: float = self.current_mission_plan.get(
                "parameter", {}).get("height", 1)

            takeoff_height = abs(z - dz)
            await self._comms.start(takeoff_height)

        await self._comms.mov_by_xyz(pos_local, yaw)

    async def scan_area(self, options: dict) -> None:
        """
        Scan a specified area using the drone's camera.

        :param options: Dictionary with 'lat', 'lon', 'height', and optional
            'yaw'.
        :type options: dict
        """
        start = (await self._comms.get_position_lat_lon_alt())[:2]
        polygon: List[tuple] = options.get("polygon", [])
        end = options.get("end_point", start)
        # polygon = [(48.767642,  11.337281),
        #            (48.767535, 11.337174),
        #            (48.767722,  11.336517),
        #            (48.768063, 11.336072),
        #            (48.768167, 11.336196)
        #            ]
        # start = (48.767642, 11.337281)
        # end = (48.767722,  11.336799)
        if "height" in options.keys():
            h: float = options["height"]
        else:
            h: float = self.current_mission_plan.get(
                "parameter", {}).get("flight_height", 5)

        mission = plan_scan(
            polygon_latlon=polygon,
            start_latlon=start,
            end_latlon=end,
            altitude=h,
            fov_deg=self._image.config.get("fov", [66, 41])[0],
            overlap_ratio=options.get("overlap_ratio", 0.2)
        )
        sp("Scan Mission Plan:")
        sp(mission)

        if not mission:
            sp("No valid scan mission plan generated")
            return
        export_geojson(mission, filename="scan_mission.geojson")

        for point in mission["route"]:
            sp(f"Scan Line: {point}")
            await self.mov({"lat": point[0], "lon": point[1],
                            "height": h, "yaw": point[2]})
            await asyncio.sleep(options.get("delay", 0.5))
