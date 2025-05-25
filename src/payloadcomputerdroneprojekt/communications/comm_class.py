from mavsdk import System
from mavsdk.offboard import PositionNedYaw, PositionGlobalYaw, VelocityNedYaw
import numpy as np
from mavsdk.telemetry import PositionVelocityNed, Position, EulerAngle
import asyncio
from payloadcomputerdroneprojekt.helper import smart_print as sp
import socket
import os
from payloadcomputerdroneprojekt.communications.helper import (
    get_data, wait_for, save_execute, get_pos_vec, reached_pos,
    rotation_matrix_yaw, abs_vel, get_vel_vec
)
from mavsdk.server_utility import StatusTextType

StatusTextType.INFO


class Communications:
    """
    Handles communication with the drone, including connection, arming,
    movement, telemetry, and image transfer.

    This class abstracts the MAVSDK API and provides high-level methods for
    controlling and monitoring the drone, as well as sending data to a ground
    station.
    """

    def __init__(self, address, config={}):
        """
        Initialize the Communications object.

        :param address: Connection address (e.g., serial:///dev/ttyAMA0:57600).
        :type address: str
        :param config: Optional configuration dictionary for communication
            settings.
        :type config: dict
        """
        self.config: dict = config
        self.address = address
        self.drone = None
        self._home_lat = None
        self._home_lon = None
        self._home_alt = None

    async def connect(self):
        """
        Establish a connection to the drone and set telemetry data rates.

        :returns: True if connection is established, False otherwise.
        :rtype: bool

        This method initializes the MAVSDK System, connects to the specified
        address, and waits until the connection is confirmed. It also sets
        telemetry data rates.
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
        """
        Check if the drone's global position is OK (GPS ready).

        :returns: True if global position is OK, False otherwise.
        :rtype: bool
        """
        return (await get_data(self.drone.telemetry.health())
                ).is_global_position_ok

    async def set_data_rates(self):
        """
        Set telemetry data rates for attitude, position, and in-air status.

        This method configures the frequency at which telemetry data is
        received.
        """
        await self.drone.telemetry.set_rate_attitude_euler(1000)
        await self.drone.telemetry.set_rate_position_velocity_ned(1000)
        await self.drone.telemetry.set_rate_position(1000)
        await self.drone.telemetry.set_rate_in_air(1000)

    async def wait_for_health(self):
        """
        Wait until both the home position and global position are OK.

        This method blocks until the drone's telemetry reports both positions
        as ready.
        """
        await wait_for(
            self.drone.telemetry.health(),
            lambda x: x.is_global_position_ok and x.is_home_position_ok)

    @save_execute("Arm")
    async def await_arm(self):
        """
        Arm the drone or wait until it is armed.

        If 'allowed_arm' is set in config, the drone will attempt to arm
        itself. Otherwise, it waits for manual arming.
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
        Disarm the drone or wait until it is disarmed.

        If 'allowed_disarm' is set in config, the drone will attempt to disarm
        itself. Otherwise, it waits for manual disarming.
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
        """
        Ensure the drone is in OFFBOARD mode.

        If not already in OFFBOARD, set the current position and start OFFBOARD
        mode if allowed by config. Otherwise, wait for manual mode switch.
        """
        mode = await get_data(self.drone.telemetry.flight_mode())
        if mode == "OFFBOARD":
            sp("-- Already in offboard mode")
        else:
            pos = await self.get_position_xyz()
            await self.drone.offboard.set_position_ned(
                PositionNedYaw(*pos[:4]))
            if self.config.get("allowed_mode_switch", True):
                sp("-- Starting offboard")
                await self.drone.offboard.start()
            else:
                await wait_for(self.drone.telemetry.flight_mode(),
                               lambda x: x == "OFFBOARD")

    async def get_relative_height(self) -> float:
        """
        Get the drone's height above the ground.

        :returns: Relative altitude in meters.
        :rtype: float
        """
        return (await get_data(self.drone.telemetry.position()
                               )).relative_altitude_m

    async def is_flighing(self) -> bool:
        """
        Check if the drone is currently flying (in air).

        :returns: True if the drone is in air, False otherwise.
        :rtype: bool
        """
        return await get_data(self.drone.telemetry.in_air())

    @save_execute("Start")
    async def start(self, height: float = 5):
        """
        Start the drone and ascend to a target height.

        :param height: Target height above ground in meters.
        :type height: float

        :returns: True if already at or above target height, otherwise None.
        :rtype: bool or None

        This method ensures OFFBOARD mode, arms the drone, checks health, and
        commands the drone to ascend if necessary.
        """
        await self._ensure_offboard()
        await self.await_arm()
        await self.check_health()
        if await self.get_relative_height() >= height:
            return True
        h = await self.get_relative_height()
        await self.mov_by_xyz([0, 0, -height-h], 0)

    async def _get_attitude(self):
        """
        Get the drone's current attitude (roll, pitch, yaw).

        :returns: List of [roll_deg, pitch_deg, yaw_deg].
        :rtype: list[float]
        """
        res: EulerAngle = await get_data(self.drone.telemetry.attitude_euler())
        return [res.roll_deg, res.pitch_deg, res.yaw_deg]

    async def _get_yaw(self):
        """
        Get the drone's current yaw angle.

        :returns: Yaw angle in degrees.
        :rtype: float
        """
        if not await self.check_health():
            sp("Telemetry not ready")
            return [0, 0, 0]
        return (await get_data(self.drone.telemetry.attitude_euler())).yaw_deg

    async def get_position_xyz(self) -> list[float]:
        """
        Get the drone's local position and attitude.

        :returns: [x, y, z, roll, pitch, yaw] in meters and degrees.
        :rtype: list[float]

        If GPS is not ready, returns zeros.
        """
        state: PositionVelocityNed = await get_data(
            self.drone.telemetry.position_velocity_ned())
        return get_pos_vec(state) + await self._get_attitude()

    async def get_position_lat_lon_alt(self):
        """
        Get the drone's global position and attitude.

        :returns: [latitude_deg, longitude_deg, relative_altitude_m, roll,
            pitch, yaw]
        :rtype: list[float]

        If GPS is not ready, returns zeros.
        """
        res: Position = await get_data(self.drone.telemetry.position())
        return [res.latitude_deg, res.longitude_deg, res.relative_altitude_m
                ] + await self._get_attitude()

    @save_execute("Move to XYZ")
    async def mov_to_xyz(self, pos: list[float], yaw: float = None):
        """
        Move the drone to a specific XYZ position in the local NED frame.

        :param pos: Target [x, y, z] position in meters.
        :type pos: list[float]
        :param yaw: Target yaw in degrees (compass). If None, uses current yaw.
        :type yaw: float, optional

        This method sends a position command and waits until the drone reaches
        the target.
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
        Move the drone with a fixed velocity in the XYZ direction.

        :param vel: Velocity vector [vx, vy, vz] in m/s (global frame).
        :type vel: list[float]
        :param yaw: Yaw angle in degrees (relative to North). If None, uses
            current yaw.
        :type yaw: float, optional

        This method sends a velocity command to the drone.
        """
        if yaw is None:
            yaw = await self._get_yaw()
        await self.drone.offboard.set_velocity_ned(VelocityNedYaw(
            north_m_s=vel[0], east_m_s=vel[1], down_m_s=vel[2], yaw_deg=yaw))

    @save_execute("Move by Velocity")
    async def mov_by_vel(self, vel: list[float], yaw: float = 0):
        """
        Move the drone with velocity relative to its current yaw orientation.

        :param vel: Velocity vector [vx, vy, vz] in drone's yaw frame.
        :type vel: list[float]
        :param yaw: Additional yaw to add to current yaw (degrees).
        :type yaw: float, optional

        This method rotates the velocity vector by the current yaw and sends
        the command.
        """
        old_yaw = await self._get_yaw()
        new_vel = rotation_matrix_yaw(old_yaw) @ np.array(vel)
        await self.mov_with_vel(new_vel[0], old_yaw + yaw)

    @save_execute("Move by XYZ")
    async def mov_by_xyz(self, pos: list[float], yaw: float = 0):
        """
        Move the drone by a relative XYZ offset in its local yaw frame.

        :param pos: Offset [dx, dy, dz] in meters (drone's yaw frame).
        :type pos: list[float]
        :param yaw: Additional yaw to add to current yaw (degrees).
        :type yaw: float, optional

        This method computes the new position and sends a move command.
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
        Move the drone by a relative XYZ offset in the local reference frame.

        :param pos: Offset [dx, dy, dz] in meters (NED frame).
        :type pos: list[float]
        :param yaw: Target yaw in degrees (absolute).
        :type yaw: float, optional

        This method computes the new position and sends a move command.
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
        Move the drone to a specific latitude, longitude, and altitude.

        :param pos: [latitude_deg, longitude_deg, relative_altitude_m].
        :type pos: list[float]
        :param yaw: Target yaw in degrees. If None, uses current yaw.
        :type yaw: float, optional

        This method sends a global position command and waits until the drone
        reaches the target.
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
        Land the drone using the standard land mode.

        This method triggers the drone's landing procedure.
        """
        await self.drone.action.land()

    async def receive_mission_file(self, func_on_receive):
        """
        Placeholder for receiving a mission file from the ground station.

        :param func_on_receive: Callback function to execute when a file is
            received.
        :type func_on_receive: callable

        This method is not yet implemented.
        """
        while True:
            await asyncio.sleep(2)
        pass

    async def send_found_obj(obj: dict):
        """
        Placeholder for sending information about a found object.

        :param obj: Dictionary containing object information.
        :type obj: dict

        This method is not yet implemented.
        """
        pass

    @save_execute("Send Image")
    async def send_image(self, path: str) -> bool:
        """
        Send an image file to the ground station over WiFi using TCP sockets.

        :param path: File path to the image on the Raspberry Pi.
        :type path: str

        :returns: True if the image was sent successfully, False otherwise.
        :rtype: bool

        This method opens a TCP connection to the ground station, sends the
        file size, and then streams the image data in chunks. Handles network
        and file errors.
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

    async def send_status(self, status: str):
        """
        Send a status text message to the ground station.

        :param status: Status message to send.
        :type status: str

        This method uses the MAVSDK server utility to send a status text.
        """
        await self.drone.server_utility.send_status_text(
            StatusTextType.INFO, status)
