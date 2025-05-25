import math
from mavsdk import System
from mavsdk.offboard \
    import PositionNedYaw, PositionGlobalYaw, VelocityNedYaw
import numpy as np
from scipy.spatial.transform import Rotation as R
from mavsdk.telemetry import PositionVelocityNed, PositionNed, VelocityNed, \
    Position, EulerAngle
import asyncio
import aiohttp
import os


def save_execute(msg):
    def wrapper(f):
        def wrap(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                print(f"{msg}, Error: {e}")
        return wrap
    return wrapper


class Communications:
    def __init__(self, address, config={}):
        self.config: dict = config
        self.address = address
        self.drone = None
        self._home_lat = None
        self._home_lon = None
        self._home_alt = None

    async def connect(self):
        """
        Establish a connection to the drone. Initializes the System object,
        connects to the specified address, and verifies the connection.

        Parameters:
            address (str):
                Connection address (e.g., serial:///dev/ttyAMA0:57600).
                Defaults to "serial:///dev/ttyAMA0:57600" if not provided.

        Returns:
            bool:
                True if the connection is successfully established,
                False otherwise.
        """
        if self.drone is None:
            self.drone = System()
            print("-- System initialized")

        print(f"Connecting to drone at {self.address} ...")

        await self.drone.connect(system_address=self.address)
        await wait_for(self.drone.core.connection_state(),
                       lambda x: x.is_connected)
        print("-- Connection established successfully")

    async def check_health(self) -> bool:
        """Return if GPS Position is Okay

        Returns:
            bool:
        """
        return (await get_data(self.drone.telemetry.health())
                ).is_global_position_ok

    async def wait_for_health(self):
        """
        Runs unit the home position and global position is okay.
        """
        await wait_for(
            self.drone.telemetry.health(),
            lambda x: x.is_global_position_ok and x.is_home_position_ok)

    @save_execute("Arm")
    async def await_arm(self):
        """
        Arms or wait until the drone is armed
        """
        if self.config.get("allowed_arm", False):
            try:
                await self.drone.action.arm()
            except Exception as e:
                print(f"self arming failed waiting for manuel: {e}")
        await wait_for(self.drone.telemetry.armed(), lambda x: x)
        print("Drone armed")

    @save_execute("Disarm")
    async def await_disarm(self):
        """
        Disarms or wait until the drone is disarmed
        """
        if self.config.get("allowed_disarm", False):
            try:
                await self.drone.action.disarm()
            except Exception as e:
                print(f"self arming failed waiting for manuel: {e}")
        await wait_for(self.drone.telemetry.armed(), lambda x: not x)
        print("Drone disarmed")

    @save_execute("Ensure Offboard")
    async def _ensure_offboard(self):
        mode = await get_data(self.drone.telemetry.flight_mode())
        if mode == "OFFBOARD":
            print("-- Already in offboard mode")
        else:
            await self.drone.offboard.set_position_ned(
                PositionNedYaw(0.0, 0.0, 0.0, 0.0))
            if self.config.get("allowed_mode_switch", True):
                # check if this would work
                print("-- Starting offboard")
                await self.drone.offboard.start()
            else:
                await wait_for(self.drone.telemetry.flight_mode(),
                               lambda x: x == "OFFBOARD")

    async def get_relative_height(self) -> float:
        """
        Get height estimation to the ground
        Returns:
            _type_: _description_
        """
        if not await self.check_health():
            print("Telemetry not ready")
            return -5.
        return (await get_data(self.drone.telemetry.position()
                               )).relative_altitude_m

    async def is_flighing(self) -> bool:
        """
        Checks if drone is currently flighing

        Returns:
            bool:
        """
        return await get_data(self.drone.telemetry.in_air())

    @save_execute("Start")
    async def start(self, height: float = 5):
        """
        Starts the drone and run it until it reached the target height or is
        heigher

        Args:
            height (float, optional): Height over the ground. Defaults to 5.

        Returns:
            _type_: _description_
        """
        await self.await_arm()
        if await self.get_relative_height() >= height:
            return True
        await self.check_health()
        await self._ensure_offboard()
        h = await self.get_relative_height()
        await self.mov_by_xyz([0, 0, -height-h], 0)

    async def _get_attitude(self):
        # Timspektion
        if not await self.check_health():
            print("Telemetry not ready")
            return [0, 0, 0]
        res: EulerAngle = await get_data(self.drone.telemetry.attitude_euler())
        return [res.roll_deg, res.pitch_deg, res.yaw_deg]

    async def _get_yaw(self):
        if not await self.check_health():
            print("Telemetry not ready")
            return [0, 0, 0]
        return (await get_data(self.drone.telemetry.attitude_euler())).yaw_deg

    async def get_position_xyz(self) -> list[float]:
        """
        Returns list of floating point values. If the gps is not ready it will
        return zeros but not wait until it is ready.

        Returns:
            list[float]: x, y, z, roll, pitch, yaw
        """
        if not await self.check_health():
            print("Telemetry not ready")
            return [0, 0, 0, 0, 0, 0]
        state: PositionVelocityNed = await get_data(
            self.drone.telemetry.position_velocity_ned())
        return get_pos_vec(state) + await self._get_attitude()

    async def get_position_lat_lon_alt(self):
        """
        Returns list of floating point values. If the gps is not ready it will
        return zeros but not wait until it is ready.
        [m, degree]
        Returns:
            list[float]: lat, lon, alt, roll, pitch, yaw
        """
        if not await self.check_health():
            print("Telemetry not ready")
            return [0, 0, 0, 0, 0, 0]
        res: Position = await get_data(self.drone.telemetry.position())
        return [res.latitude_deg, res.longitude_deg, res.absolute_altitude_m
                ] + await self._get_attitude()

    @save_execute("Move to XYZ")
    async def mov_to_xyz(self, pos: list[float], yaw: float = None):
        """
        Move to the XYZ coordinates, XYZ is fixed to the start position and yaw
        0 is North.

        Args:
            pos (list[float]): XYZ [m] coordinates in local ned values
            yaw (float, optional): target yaw [degree] in compass values
        """
        if yaw is None:
            yaw = await self._get_yaw()
        await self.drone.offboard.set_position_ned(PositionNedYaw(
            north_m=pos[0], east_m=pos[1], down_m=pos[2], yaw_deg=yaw))
        await wait_for(
            self.drone.telemetry.position_velocity_ned(),
            reached_pos(pos, self.config.get("pos_error", 0.75),
                        self.config.get("vel_error", 0.5)))

    @save_execute("Move with Velocity")
    async def mov_with_vel(self, vel: list[float], yaw: float = None):
        """
        Move the drone with a fixed velocity in XYZ direction [m/s].
        XYZ in global position system

        Args:
            vel (list[float]):
            yaw (float, optional): Realtiv to North [degree]
        """
        if yaw is None:
            yaw = await self._get_yaw()
        await self.drone.offboard.set_velocity_ned(VelocityNedYaw(
            north_m_s=vel[0], east_m_s=vel[1], down_m_s=vel[2], yaw_deg=yaw))

    @save_execute("Move by Velocity")
    async def mov_by_vel(self, vel: list[float], yaw: float = 0):
        """
        Move the drone rotated to drone yaw coordinates

        Args:
            vel (list[float]): Velocity orientated to drone yaw
            yaw (float, optional):  Adds the
                yaw to the current one. Defaults to 0.
        """
        old_yaw = await self._get_yaw()
        new_vel = rotation_matrix_yaw(old_yaw) @ np.array(vel)
        await self.mov_with_vel(new_vel[0], old_yaw + yaw)

    @save_execute("Move by XYZ")
    async def mov_by_xyz(self, pos: list[float], yaw: float = 0):
        """
        Move the drone by XYZ in local drone yaw coordinates

        Args:
            pos(list[float]):
            yaw(float, optional): Adds the
                yaw to the current one. Defaults to 0.
        """
        pos = np.array(pos)
        cur_pos = await self.get_position_xyz()
        yaw_cur = cur_pos[5]
        yaw += yaw_cur
        cur_pos = np.array(cur_pos[:3])
        new_pos = cur_pos + rotation_matrix_yaw(yaw_cur) @ pos
        await self.mov_to_xyz(new_pos[0], yaw)

    @save_execute("Move by XYZ old")
    async def mov_by_xyz_old(self, pos: list[float], yaw: float = 0):
        """
        Move the drone by XYZ in local reference frame. Yaw = 0 => North

        Args:
            pos(g):
            yaw(float, optional): Sets the new yaw as target. Defaults to 0.
        """
        pos = np.array(pos)
        cur_pos = await self.get_position_xyz()
        yaw += cur_pos[5]
        cur_pos = np.array(cur_pos[:3])
        new_pos = cur_pos + pos
        await self.mov_to_xyz(new_pos, yaw)

    @save_execute("Move to Lat Lon Alt")
    async def mov_to_lat_lon_alt(self, pos: list[float], yaw: float = None):
        """
        Move the drone to the lat lon global coordinates with a relativ height
        and a target yaw.

        Args:
            pos (list[float]): [lat, lon, delta_h] [degree, degree, m]
            yaw (float, optional): [degree]. Defaults to current.

        """
        if yaw is None:
            yaw = await self._get_yaw()
        await self.drone.offboard.set_position_global(PositionGlobalYaw(
            lat_deg=pos[0], lon_deg=pos[1], alt_m=pos[2], yaw_deg=yaw,
            altitude_type=PositionGlobalYaw.AltitudeType(0)))

        def reach_func(state: Position):
            return (abs(state.latitude_deg - pos[0]
                        ) < self.config.get("degree_error", 0.00001) and
                    abs(state.longitude_deg - pos[1]
                        ) < self.config.get("degree_error", 0.00001) and
                    abs(state.absolute_altitude_m - pos[2]
                        ) < self.config.get("pos_error", 0.75))

        await wait_for(self.drone.telemetry.position(), reach_func)
        await wait_for(self.drone.telemetry.position_velocity_ned(),
                       lambda x: abs_vel(
                           get_pos_vec(x)) < self.config.get("vel_error", 0.5))

    @save_execute("Land")
    async def land(self):
        """
        Trigger standard land mode of the drone.
        """
        await self.drone.action.land()

    def receive_mission_file():
        pass

    @save_execute("Send File")
    async def send_file(self, file_path: str, endpoint: str) -> bool:
        """
        Send a file to the laptop over WiFi using an HTTP POST request.

        Parameters:
            file_path (str): Path to the file to send.
            endpoint (str): Flask endpoint URL (e.g., 'http://192.168.1.100:5000/upload').

        Returns:
            bool: True if the file was sent successfully, False otherwise.
        """
        if not os.path.isfile(file_path):
            print(f"Error: File not found at {file_path}")
            return False
        if os.path.getsize(file_path) == 0:
            print("Error: File is empty")
            return False

        try:
            async with asyncio.timeout(self.config.get("network_timeout", 10)):
                async with aiohttp.ClientSession() as session:
                    with open(file_path, 'rb') as f:
                        # Prepare multipart form data
                        data = aiohttp.FormData()
                        data.add_field('file', f, filename=os.path.basename(file_path))

                        # Send POST request
                        async with session.post(endpoint, data=data) as response:
                            if response.status == 200:
                                print(f"File sent successfully: {file_path}")
                                return True
                            else:
                                print(f"HTTP error: Status {response.status}")
                                return False

        except asyncio.TimeoutError:
            print("Network timeout while sending file")
            return False
        except aiohttp.ClientError as e:
            print(f"Network error while sending file: {e}")
            return False
        except Exception as e:
            print(f"Error sending file: {e}")
            return False

    @save_execute("Send Found Objects")
    async def send_found_objects(self, file_path: str) -> bool:
        """
        Send an existing file containing found objects to the laptop over WiFi by calling send_file.

        Parameters:
            file_path (str): Path to the existing file (e.g., JSON or CSV) on the Raspberry Pi.

        Returns:
            bool: True if the file was sent successfully, False otherwise.
        """
        # Validate file
        if not os.path.isfile(file_path):
            print(f"Error: Objects file not found at {file_path}")
            return False
        if os.path.getsize(file_path) == 0:
            print("Error: Objects file is empty")
            return False
        if not file_path.lower().endswith(('.json', '.csv')):
            print(f"Warning: File {file_path} may not be a valid objects file (expected .json or .csv)")

        # Get laptop URL from config
        laptop_url = self.config.get("laptop_url_objects", "http://192.168.1.100:5000/upload_objects")

        # Delegate to send_file
        result = await self.send_file(file_path, laptop_url)
        if result:
            print(f"Objects file sent successfully: {file_path}")
        return result

    @save_execute("Send Image")
    async def send_image(self, path: str) -> bool:
        """
        Send an image file to the laptop over WiFi by calling send_file.

        Parameters:
            path (str): File path to the image on the Raspberry Pi.

        Returns:
            bool: True if the image was sent successfully, False otherwise.
        """
        # Validate file
        if not os.path.isfile(path):
            print(f"Error: Image file not found at {path}")
            return False
        if os.path.getsize(path) == 0:
            print("Error: Image file is empty")
            return False
        if not path.lower().endswith(('.jpg', '.jpeg', '.png')):
            print(f"Warning: File {path} may not be a valid image (expected .jpg, .jpeg, .png)")

        # Get laptop URL from config
        laptop_url = self.config.get("laptop_url", "http://192.168.1.100:5000/upload")

        # Delegate to send_file
        return await self.send_file(path, laptop_url)

    def send_status(status: str):
        pass


def reached_pos(target: list, error=0.5, error_vel=0.1):
    def func(state: PositionVelocityNed):
        return (pythagoras(get_pos_vec(state), target) < error
                ) and (abs_vel(get_vel_vec(state)) < error_vel)
    return func


def get_pos_vec(state: PositionVelocityNed):
    pos: PositionNed = state.position
    return [pos.north_m, pos.east_m, pos.down_m]


def get_vel_vec(state: PositionVelocityNed):
    pos: VelocityNed = state.velocity
    return [pos.north_m_s, pos.east_m_s, pos.down_m_s]


def abs_vel(vec):
    return math.sqrt(
        sum([v**2 for v in vec]))


def pythagoras(pos_a, pos_b):
    return math.sqrt(
        sum([(pos_a[i] - pos_b[i])**2 for i in range(len(pos_a))]))


async def get_data(func):
    async for res in func:
        return res


async def wait_for(func, b):
    async for res in func:
        if b(res):
            return res


def rotation_matrix_yaw(rot):
    return R.from_euler('z', [rot], degrees=True).as_matrix()
