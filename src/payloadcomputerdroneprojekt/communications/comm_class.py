from mavsdk import System
from mavsdk.offboard import PositionNedYaw, PositionGlobalYaw, VelocityNedYaw
from mavsdk.telemetry import PositionVelocityNed, Position, EulerAngle
import numpy as np
from payloadcomputerdroneprojekt.helper import smart_print as sp
from payloadcomputerdroneprojekt.communications.helper import (
    get_data, wait_for, save_execute, get_pos_vec, reached_pos,
    rotation_matrix_yaw, abs_vel, get_vel_vec
)
from mavsdk.server_utility import StatusTextType
from typing import Any, Optional, Dict, List


class Communications:
    """
    Handles communication with the drone, including connection, arming,
    movement, telemetry, and image transfer.

    This class abstracts the MAVSDK API and provides high-level methods for
    controlling and monitoring the drone, as well as sending data to a ground
    station.
    """

    def __init__(self, address: str, config: Optional[Dict[str, Any]] = None
                 ) -> None:
        """
        Initialize the Communications object.

        :param address: Connection address (e.g., serial:///dev/ttyAMA0:57600).
        :type address: str
        :param config: Optional configuration dictionary for communication
            settings.
        :type config: dict
        """
        self.config: Dict[str, Any] = config if config is not None else {}
        self.address: str = address
        self.drone: Optional[System] = None

    async def connect(self) -> bool:
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
        await self.drone.connect(system_address=self.address)
        await wait_for(self.drone.core.connection_state(),
                       lambda x: x.is_connected)

        # await self.set_data_rates()
        sp("-- Connection established successfully")
        return True

    async def check_health(self) -> bool:
        """
        Check if the drone's global position is OK (GPS ready).

        :returns: True if global position is OK, False otherwise.
        :rtype: bool
        """
        return (await get_data(self.drone.telemetry.health())
                ).is_global_position_ok

    async def set_data_rates(self) -> None:
        """
        Set telemetry data rates for attitude, position, and in-air status.

        This method configures the frequency at which telemetry data is
        received.
        """
        await self.drone.telemetry.set_rate_attitude_euler(100)
        await self.drone.telemetry.set_rate_position_velocity_ned(100)
        await self.drone.telemetry.set_rate_position(100)
        await self.drone.telemetry.set_rate_in_air(100)

    async def wait_for_health(self) -> None:
        """
        Wait until both the home position and global position are OK.

        This method blocks until the drone's telemetry reports both positions
        as ready.
        """
        await wait_for(
            self.drone.telemetry.health(),
            lambda x: x.is_global_position_ok and x.is_home_position_ok)

    @save_execute("Arm")
    async def await_arm(self) -> None:
        """
        Arm the drone or wait until it is armed.

        If 'allowed_arm' is set in config, the drone will attempt to arm
        itself. Otherwise, it waits for manual arming.
        """
        if self.config.get("allowed_arm", False):
            try:
                await self.drone.action.arm()
            except Exception as exc:
                sp(f"self arming failed waiting for manual: {exc}")
        sp("Awaiting arming")
        await wait_for(self.drone.telemetry.armed(), lambda x: x)
        sp("Drone armed")

    @save_execute("Disarm")
    async def await_disarm(self) -> None:
        """
        Disarm the drone or wait until it is disarmed.

        If 'allowed_disarm' is set in config, the drone will attempt to disarm
        itself. Otherwise, it waits for manual disarming.
        """
        if self.config.get("allowed_disarm", False):
            try:
                await self.drone.action.disarm()
            except Exception as exc:
                sp(f"self arming failed waiting for manual: {exc}")
        await wait_for(self.drone.telemetry.armed(), lambda x: not x)
        sp("Drone disarmed")

    @save_execute("Ensure Offboard")
    async def _ensure_offboard(self) -> None:
        """
        Ensure the drone is in OFFBOARD mode.

        If not already in OFFBOARD, set the current position and start OFFBOARD
        mode if allowed by config. Otherwise, wait for manual mode switch.
        """
        flight_mode = await get_data(self.drone.telemetry.flight_mode())
        if flight_mode == "OFFBOARD":
            sp("-- Already in offboard mode")
        else:
            position = await self.get_position_xyz()
            await self.drone.offboard.set_position_ned(
                PositionNedYaw(*position[:4]))

            sp("-- Starting offboard")
            await self.drone.offboard.start()

    async def get_relative_height(self) -> float:
        """
        Get the drone's height above the ground.

        :returns: Relative altitude in meters.
        :rtype: float
        """
        return (await get_data(self.drone.telemetry.position()
                               )).relative_altitude_m

    async def is_flying(self) -> bool:
        """
        Check if the drone is currently flying (in air).

        :returns: True if the drone is in air, False otherwise.
        :rtype: bool
        """
        return await get_data(self.drone.telemetry.in_air())

    async def landed(self) -> bool:
        """
        Check if the drone is currently flying (in air).

        :returns: True if the drone is in air, False otherwise.
        :rtype: bool
        """
        return await wait_for(self.drone.telemetry.in_air(),
                              lambda x: not x)

    @save_execute("Start")
    async def start(self, height: float = 5) -> Optional[bool]:
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
        await self.mov_by_xy([0, 0, -height], 0)

    async def _get_attitude(self) -> List[float]:
        """
        Get the drone's current attitude (roll, pitch, yaw).

        :returns: List of [roll_deg, pitch_deg, yaw_deg].
        :rtype: list[float]
        """
        euler: EulerAngle = await get_data(
            self.drone.telemetry.attitude_euler())
        return [euler.roll_deg, euler.pitch_deg, euler.yaw_deg]

    async def _get_yaw(self) -> float:
        """
        Get the drone's current yaw angle.

        :returns: Yaw angle in degrees.
        :rtype: float
        """
        return (await get_data(self.drone.telemetry.attitude_euler())).yaw_deg

    async def get_position_xyz(self) -> List[float]:
        """
        Get the drone's local position and attitude.

        :returns: [x, y, z, roll, pitch, yaw] in meters and degrees.
        :rtype: list[float]

        If GPS is not ready, returns zeros.
        """
        state: PositionVelocityNed = await get_data(
            self.drone.telemetry.position_velocity_ned())
        return get_pos_vec(state) + await self._get_attitude()

    async def get_position_lat_lon_alt(self) -> List[float]:
        """
        Get the drone's global position and attitude.

        :returns: [latitude_deg, longitude_deg, relative_altitude_m, roll,
            pitch, yaw]
        :rtype: list[float]

        If GPS is not ready, returns zeros.
        """
        position: Position = await get_data(self.drone.telemetry.position())
        return [position.latitude_deg, position.longitude_deg,
                position.relative_altitude_m] + await self._get_attitude()

    @save_execute("Move to XYZ")
    async def mov_to_xyz(self, pos: List[float], yaw: Optional[float] = None
                         ) -> None:
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
            reached_pos(pos, self.config.get("pos_error", 0.2),
                        self.config.get("vel_error", 0.5)))

    @save_execute("Move with Velocity")
    async def mov_with_vel(self, velocity: List[float],
                           yaw: Optional[float] = None
                           ) -> None:
        """
        Move the drone with a fixed velocity in the XYZ direction.

        :param velocity: Velocity vector [vx, vy, vz] in m/s (global frame).
        :type velocity: list[float]
        :param yaw: Yaw angle in degrees (relative to North). If None, uses
            current yaw.
        :type yaw: float, optional

        This method sends a velocity command to the drone.
        """
        if yaw is None:
            yaw = await self._get_yaw()
        await self.drone.offboard.set_velocity_ned(VelocityNedYaw(
            north_m_s=velocity[0], east_m_s=velocity[1],
            down_m_s=velocity[2], yaw_deg=yaw))

    @save_execute("Move by Velocity")
    async def mov_by_vel(self, velocity: List[float], yaw: float = 0) -> None:
        """
        Move the drone with velocity relative to its current yaw orientation.

        :param velocity: Velocity vector [vx, vy, vz] in drone's yaw frame.
        :type velocity: list[float]
        :param yaw: Additional yaw to add to current yaw (degrees).
        :type yaw: float, optional

        This method rotates the velocity vector by the current yaw and sends
        the command.
        """
        current_yaw = await self._get_yaw()
        rotated_velocity = rotation_matrix_yaw(
            current_yaw) @ np.array(velocity)
        total_yaw = (yaw + current_yaw) % 360
        await self.mov_with_vel(rotated_velocity[0].tolist(),
                                total_yaw)

    @save_execute("Move by XYZ")
    async def mov_by_xyz(self, offset: List[float], yaw: float = 0) -> None:
        """
        Move the drone by a relative XYZ offset in its local yaw frame.

        :param offset: Offset [dx, dy, dz] in meters (drone's yaw frame).
        :type offset: list[float]
        :param yaw: Additional yaw to add to current yaw (degrees).
        :type yaw: float, optional

        This method computes the new position and sends a move command.
        """
        offset_arr = np.array(offset)
        current_position = await self.get_position_xyz()
        current_yaw = current_position[5]
        total_yaw = (yaw + current_yaw) % 360
        current_position_arr = np.array(current_position[:3])
        new_position = current_position_arr + \
            rotation_matrix_yaw(current_yaw) @ offset_arr
        await self.mov_to_xyz(new_position[0].tolist(), total_yaw)

    @save_execute("Move by XYZ")
    async def mov_by_xy(self, offset: List[float], yaw: float = 0) -> None:
        """
        Move the drone by a relative XY offset in the local yaw frame.
        :param offset: Offset [dx, dy, z] in meters (drone's yaw frame).
        :type offset: list[float]
        """
        offset_arr = np.array(offset)
        current_position = await self.get_position_xyz()
        current_yaw = current_position[5]
        total_yaw = (yaw + current_yaw) % 360
        current_position_arr = np.array(current_position[:3])
        current_position_arr[2] = 0
        new_position = current_position_arr + \
            rotation_matrix_yaw(current_yaw) @ offset_arr
        await self.mov_to_xyz(new_position[0].tolist(), total_yaw)

    @save_execute("Move by XYZ old")
    async def mov_by_xyz_old(self, offset: List[float],
                             yaw: float = 0) -> None:
        """
        Move the drone by a relative XYZ offset in the local reference frame.

        :param offset: Offset [dx, dy, dz] in meters (NED frame).
        :type offset: list[float]
        :param yaw: Target yaw in degrees (absolute).
        :type yaw: float, optional

        This method computes the new position and sends a move command.
        """
        offset_arr = np.array(offset)
        current_position = await self.get_position_xyz()
        current_yaw = current_position[5]
        total_yaw = (yaw + current_yaw) % 360
        current_position_arr = np.array(current_position[:3])
        new_position = current_position_arr + offset_arr
        await self.mov_to_xyz(new_position.tolist(), total_yaw)

    @save_execute("Move to Lat Lon Alt")
    async def mov_to_lat_lon_alt(self, pos: List[float],
                                 yaw: Optional[float] = None) -> None:
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
        # TODO: check if type 2 is better
        await self.drone.offboard.set_position_global(PositionGlobalYaw(
            lat_deg=pos[0], lon_deg=pos[1], alt_m=pos[2], yaw_deg=yaw,
            altitude_type=PositionGlobalYaw.AltitudeType(0)))

        def reach_func(state: Position) -> bool:
            return (abs(state.latitude_deg - pos[0]
                        ) < self.config.get("degree_error", 1/110000) and
                    abs(state.longitude_deg - pos[1]
                        ) < self.config.get("degree_error", 1/110000))

        await wait_for(self.drone.telemetry.position(), reach_func)
        sp("reached pos")
        await wait_for(self.drone.telemetry.position_velocity_ned(),
                       lambda x: abs_vel(
                           get_vel_vec(x)) < self.config.get("vel_error", 0.5))
        sp("reached point")

    @save_execute("Land")
    async def land(self) -> None:
        """
        Land the drone using the standard land mode.

        This method triggers the drone's landing procedure.
        """
        await self.drone.action.land()

    async def send_status(self, status: str) -> None:
        """
        Send a status text message to the ground station.

        :param status: Status message to send.
        :type status: str

        This method uses the MAVSDK server utility to send a status text.
        """
        if not self.drone or not hasattr(self.drone, 'server_utility'):
            sp("Drone not connected or server utility not available.")
            return
        await self.drone.server_utility.send_status_text(
            StatusTextType.INFO, status)
