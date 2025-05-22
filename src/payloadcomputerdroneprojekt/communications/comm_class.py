from mavsdk import System
from mavsdk.offboard \
    import PositionNedYaw, PositionGlobalYaw, VelocityNedYaw
import numpy as np
from mavsdk.telemetry import PositionVelocityNed, Position, EulerAngle
import asyncio
from payloadcomputerdroneprojekt.helper import smart_print as sp
import socket
import os
from payloadcomputerdroneprojekt.communications.helper import\
    get_data, wait_for, save_execute, get_pos_vec, reached_pos, \
    rotation_matrix_yaw, abs_vel, get_vel_vec


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
            sp("-- System initialized")

        sp(f"Connecting to drone at {self.address} ...")
        if "action" not in self.drone._plugins or \
                not (await get_data(self.drone.core.connection_state())
                     ).is_connected:
            await self.drone.connect(system_address=self.address)
            await wait_for(self.drone.core.connection_state(),
                           lambda x: x.is_connected)

            await self.set_data_rates()

        sp("-- Connection established successfully")

    async def check_health(self) -> bool:
        """Return if GPS Position is Okay

        Returns:
            bool:
        """
        return (await get_data(self.drone.telemetry.health())
                ).is_global_position_ok

    async def set_data_rates(self):
        await self.drone.telemetry.set_rate_attitude_euler(1000)
        await self.drone.telemetry.set_rate_position_velocity_ned(1000)
        await self.drone.telemetry.set_rate_position(1000)
        await self.drone.telemetry.set_rate_in_air(1000)

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
                sp(f"self arming failed waiting for manuel: {e}")
        sp("Awaiting arming")
        await wait_for(self.drone.telemetry.armed(), lambda x: x)
        sp("Drone armed")

    @save_execute("Disarm")
    async def await_disarm(self):
        """
        Disarms or wait until the drone is disarmed
        """
        if self.config.get("allowed_disarm", False):
            try:
                await self.drone.action.disarm()
            except Exception as e:
                sp(f"self arming failed waiting for manuel: {e}")
        await wait_for(self.drone.telemetry.armed(), lambda x: not x)
        sp("Drone disarmed")

    @save_execute("Ensure Offboard")
    async def _ensure_offboard(self):
        mode = await get_data(self.drone.telemetry.flight_mode())
        if mode == "OFFBOARD":
            sp("-- Already in offboard mode")
        else:
            pos = await self.get_position_xyz()
            await self.drone.offboard.set_position_ned(
                PositionNedYaw(*pos[:4]))
            if self.config.get("allowed_mode_switch", True):
                # check if this would work
                sp("-- Starting offboard")
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
        await self._ensure_offboard()
        await self.await_arm()
        await self.check_health()
        if await self.get_relative_height() >= height:
            return True
        h = await self.get_relative_height()
        await self.mov_by_xyz([0, 0, -height-h], 0)

    async def _get_attitude(self):
        # Timspektion
        res: EulerAngle = await get_data(self.drone.telemetry.attitude_euler())
        return [res.roll_deg, res.pitch_deg, res.yaw_deg]

    async def _get_yaw(self):
        if not await self.check_health():
            sp("Telemetry not ready")
            return [0, 0, 0]
        return (await get_data(self.drone.telemetry.attitude_euler())).yaw_deg

    async def get_position_xyz(self) -> list[float]:
        """
        Returns list of floating point values. If the gps is not ready it will
        return zeros but not wait until it is ready.

        Returns:
            list[float]: x, y, z, roll, pitch, yaw
        """
        state: PositionVelocityNed = await get_data(
            self.drone.telemetry.position_velocity_ned())
        return get_pos_vec(state) + await self._get_attitude()

    async def get_position_lat_lon_alt(self):
        """
        Returns list of floating point values. If the gps is not ready it will
        return zeros but not wait until it is ready.
        [m, degree]
        Returns:
            list[float]: lat, lon, alt_rel, roll, pitch, yaw
        """
        res: Position = await get_data(self.drone.telemetry.position())
        return [res.latitude_deg, res.longitude_deg, res.relative_altitude_m
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
                    abs(state.relative_altitude_m - pos[2]
                        ) < self.config.get("pos_error", 0.75))

        await wait_for(self.drone.telemetry.position(), reach_func)
        await wait_for(self.drone.telemetry.position_velocity_ned(),
                       lambda x: abs_vel(
                           get_vel_vec(x)) < self.config.get("vel_error", 0.5))

    @save_execute("Land")
    async def land(self):
        """
        Trigger standard land mode of the drone.
        """
        await self.drone.action.land()

    async def receive_mission_file(self, func_on_receive):
        while True:
            await asyncio.sleep(2)
        pass

    async def send_found_obj(obj: dict):
        pass

    @save_execute("Send Image")
    async def send_image(self, path: str) -> bool:
        """
        Send an image file to the laptop over WiFi using TCP sockets.

        Parameters:
            path (str): File path to the image on the Raspberry Pi.

        Returns:
            bool: True if the image was sent successfully, False otherwise.
        """
        # Validate file existence and accessibility
        if not os.path.isfile(path):
            sp(f"Error: Image file not found at {path}")
            return False

        # Get laptop IP and port from config, with defaults
        laptop_ip = self.config.get("laptop_ip", "192.168.1.100")
        laptop_port = self.config.get("laptop_port", 5000)

        try:
            # Get file size
            file_size = os.path.getsize(path)

            # Create TCP socket
            reader, writer = await asyncio.open_connection(
                laptop_ip, laptop_port)

            # Send file size first (8 bytes, big-endian)
            writer.write(file_size.to_bytes(8, byteorder='big'))
            await writer.drain()

            # Send image data in chunks
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(4096)  # 4KB chunks
                    if not chunk:
                        break
                    writer.write(chunk)
                    await writer.drain()

            # Close connection
            writer.close()
            await writer.wait_closed()
            sp(f"Image sent successfully: {path}")
            return True

        except (socket.gaierror, ConnectionRefusedError, OSError) as e:
            sp(f"Network error while sending image: {e}")
            return False
        except Exception as e:
            sp(f"Error sending image: {e}")
            return False

    async def send_status(status: str):
        pass
