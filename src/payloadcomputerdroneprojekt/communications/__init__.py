import asyncio
import math
from mavsdk import System
from mavsdk.offboard \
    import PositionNedYaw, PositionGlobalYaw, VelocityNedYaw, OffboardError


class Communications:
    def __init__(self, address):
        self.address = address
        self.drone = None
        self._home_lat = None
        self._home_lon = None
        self._home_alt = None

    async def _check_telemetry_health(self, require_home_position=False,
                                      allow_proceed_without_gps=False):
        """
        Check if telemetry is healthy (global position OK, optionally home position OK).

        Parameters:
            require_home_position (bool): Require is_home_position_ok to be True.
            allow_proceed_without_gps (bool): Return True if GPS is unavailable (for connect).

        Returns:
            bool: True if telemetry is healthy, False if not (or None for failure).
        """
        try:
            async for state in self.drone.telemetry.health():
                if state.is_global_position_ok and (
                        not require_home_position or state.is_home_position_ok
                ):
                    print("-- Telemetry healthy" +
                          (" with GPS and home position"
                           if require_home_position else ""))
                    return True
                if allow_proceed_without_gps:
                    print("Warning: Connected but GPS not ready")
                    return True
                print("Global position telemetry not available...")
                return False
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error checking telemetry health: {e}")
            return False

    async def _ensure_offboard_mode(self, set_velocity_zero=False):
        """
        Ensure the drone is in offboard mode, starting it if necessary.

        Parameters:
            set_velocity_zero (bool): Set zero velocity setpoint before starting.
        """
        try:
            if not await self.drone.offboard.is_active():
                if set_velocity_zero:
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
                await self.drone.offboard.start()
                print("-- Offboard mode activated")
            else:
                print("-- Already in offboard mode")
        except OffboardError as error:
            print(f"Offboard mode error: {error}")
            raise

    async def _get_attitude(self):
        """
        Fetch attitude data (roll, pitch, yaw) from telemetry.

        Returns:
            tuple: (roll_deg, pitch_deg, yaw_deg) or None if failed.
        """
        try:
            async for attitude in self.drone.telemetry.attitude_euler():
                return (attitude.roll_deg, attitude.pitch_deg, attitude.yaw_deg)
        except Exception as e:
            print(f"Error fetching attitude: {e}")
            return None

    async def _wait_for_armed_state(self, expect_armed=True, timeout=5.0):
        """
        Wait for the drone to reach the expected arming state.

        Parameters:
            expect_armed (bool): True to wait for armed, False for disarmed.
            timeout (float): Timeout in seconds.

        Raises:
            Exception: If the expected state is not reached within timeout.
        """
        start_time = asyncio.get_event_loop().time()
        async for armed_state in self.drone.telemetry.armed():
            if armed_state == expect_armed:
                print(
                    f"-- Drone {'armed' if expect_armed else 'disarmed'} by user via radio controller")
                return
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise Exception(
                    f"Drone {'not armed' if expect_armed else 'not disarmed'} within timeout")
            await asyncio.sleep(0.1)

    async def _get_relative_altitude(self):
        """
        Fetch relative altitude (meters above takeoff point).

        Returns:
            float: Relative altitude, or None if failed.
        """
        try:
            async for position in self.drone.telemetry.position():
                return position.relative_altitude_m
        except Exception as e:
            print(f"Error fetching relative altitude: {e}")
            return None

    async def _get_vertical_velocity(self):
        """
        Fetch vertical velocity (down_m_s, positive down).

        Returns:
            float: Vertical velocity, or None if failed.
        """
        try:
            async for state in self.drone.telemetry.position_velocity_ned():
                return state.velocity.down_m_s
        except Exception as e:
            print(f"Error fetching vertical velocity: {e}")
            return None

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
        try:
            # Initialize the System object if not already initialized
            if self.drone is None:
                self.drone = System()
                print("-- System initialized")

            # Use provided address or fallback to instance attribute
            print(f"Connecting to drone at {self.address} ...")

            # Connect to the drone
            await self.drone.connect(system_address=self.address)

            # Wait for the drone to be connected by checking for a heartbeat
            async for state in self.drone.core.connection_state():
                if state.is_connected:
                    print("-- Connection established successfully")
                    break
                await asyncio.sleep(0.5)

            # Wait for initial telemetry to ensure the drone is ready
            return await self._check_telemetry_health(allow_proceed_without_gps=True)

        except Exception as e:
            print(f"Error in connect: {e}")
            self.drone = None
            return False

    async def start(self, altitude=5.0):
        """
        Take off, rise to the altitude (default 5 m), and hover in place.
        Captures initial GPS position (if available)
        to designate as the NED (0, 0, 0) origin.
        Proceeds without GPS if unavailable.

        Parameters:
            altitude (float):
                Target altitude in meters above ground level
                (default is 5.0 meters).

        Returns:
            None:
                Arms the drone, takes off to the specified altitude,
                and maintains hover.
        """
        try:
            # Initialize home position variables
            self._home_lat = None
            self._home_lon = None
            self._home_alt = None

            # Check if the drone is connected
            # and attempt to capture GPS position
            if not await self._check_telemetry_health(require_home_position=True):
                print("GPS unavailable, proceeding without setting NED origin...")
            else:
                pos = await self.get_position_lat_lon_alt()
                if pos:
                    self._home_lat, self._home_lon, self._home_alt = pos[0], pos[1], pos[2]
                    print(
                        f"Set NED origin at GPS: (lat: {self._home_lat}, lon: {self._home_lon}, alt: {self._home_alt})")

            # Check if the drone is armed by user via radio controller
            print("Checking if drone is armed...")
            arm_timeout = 5  # seconds
            await self._wait_for_armed_state(expect_armed=True, timeout=arm_timeout)

            # Set takeoff altitude (relative to ground)
            await self.drone.action.set_takeoff_altitude(altitude)
            print(f"Commanding takeoff to {altitude} meters...")

            # Command the drone to take off
            await self.drone.action.takeoff()

            # Wait until the drone reaches approximately the target altitude
            async for position in self.drone.telemetry.position():
                if abs(position.relative_altitude_m - altitude) < 0.5:
                    print(
                        f"-- Drone reached target altitude of {altitude} meters")
                    break
                await asyncio.sleep(0.1)

            # Transition to offboard mode for hovering
            print("Switching to offboard mode...")
            await self.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -altitude, 0.0))
            await self._ensure_offboard_mode()

        except OffboardError as error:
            print(f"Offboard mode error: {error}")
            await self.drone.offboard.stop()
            await self.drone.action.land()
        except Exception as e:
            print(f"Error in start: {e}")
            await self.drone.action.land()

    async def land(self):
        """
        Command the drone to land from its current altitude.
        Uses offboard mode for precise velocity control during
        the final phase and ensures a smooth landing.

        Returns:
            None: Manages the descent, lands the drone, and confirms it is disarmed by the user.
        """
        try:
            # Get the current altitude to confirm starting position
            relative_altitude = await self._get_relative_altitude()
            if relative_altitude is None:
                raise Exception("Failed to get current altitude")
            print(f"Current altitude: {relative_altitude} meters")

            # Transition to offboard mode for controlled descent
            print("Switching to offboard mode for controlled descent...")
            await self._ensure_offboard_mode(set_velocity_zero=True)

            # Phase 1: Descend to 0.5 meters at a moderate speed (0.5 m/s)
            target_altitude = 0.5
            descent_speed = 0.5
            if relative_altitude > target_altitude:
                print(
                    f"Descending to {target_altitude} meters at {descent_speed} m/s...")
                async for position in self.drone.telemetry.position():
                    await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, descent_speed, 0.0))
                    if position.relative_altitude_m <= target_altitude + 0.1:
                        print("-- Reached altitude 0.5 meters")
                        break
                    await asyncio.sleep(0.1)

            # Phase 2: Slow descent at 0.1 m/s for the final 0.5 meters
            slow_descent_speed = 0.1
            print(
                f"Descending final 0.5 meters at {slow_descent_speed} m/s...")
            async for position in self.drone.telemetry.position():
                await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, slow_descent_speed, 0.0))
                if position.relative_altitude_m <= 0.1:
                    print("Drone near ground, initiating final landing...")
                    break
                await asyncio.sleep(0.1)

            # Command final landing and wait for completion
            await self.drone.action.land()
            print("Commanding landing...")
            async for state in self.drone.telemetry.in_air():
                if not state:
                    print("-- Drone has landed")
                    break
                await asyncio.sleep(0.1)

            # Stop offboard mode
            await self.drone.offboard.stop()
            print("-- Offboard mode stopped")

            # Check if the drone is disarmed by user via radio controller
            print("Checking if drone is disarmed...")
            disarm_timeout = 5  # seconds
            await self._wait_for_armed_state(expect_armed=False, timeout=disarm_timeout)

        except OffboardError as error:
            print(f"Offboard mode error: {error}")
            await self.drone.offboard.stop()
            await self.drone.action.land()
        except Exception as e:
            print(f"Error in land: {e}")
            await self.drone.offboard.stop()
            await self.drone.action.land()

    async def mov_to_xyz(self, pos, yaw):
        """
        Move the drone to a specified position (x, y, z)
        in the NED coordinate system with a given yaw angle.

        Parameters:
            pos (list or tuple):
                Position vector [x, y, z] in meters in the local NED frame.
            yaw (float):
                Yaw angle in degrees (0 = North, positive = clockwise).

        Returns:
            None:
                Sends the position setpoint
                and waits for the drone to reach the target.
        """
        try:
            # Ensure the drone is in offboard mode
            await self._ensure_offboard_mode()

            # Create a position setpoint in NED coordinates
            position_setpoint = PositionNedYaw(
                north_m=pos[0], east_m=pos[1], down_m=pos[2], yaw_deg=yaw)

            # Send the position setpoint to the drone
            await self.drone.offboard.set_position_ned(position_setpoint)
            print(
                f"Commanded drone to move to position ({pos[0]}, {pos[1]}, {pos[2]}) with yaw {yaw} degrees...")

            # Monitor the drone's position to confirm it has reached the target
            async for state in self.drone.telemetry.position_velocity_ned():
                if (
                    abs(state.position.north_m - pos[0]) < 0.5 and
                    abs(state.position.east_m - pos[1]) < 0.5 and
                    abs(state.position.down_m - pos[2]) < 0.5
                ):
                    print("-- Drone reached target position")
                    break
                # Throttle polling to 10 Hz to reduce CPU load
                await asyncio.sleep(0.1)

        except OffboardError as error:
            print(f"Offboard mode error: {error}")
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error in mov_to_xyz: {e}")
            await self.drone.offboard.stop()

    async def mov_to_lat_lon_alt(self, pos, yaw):
        """
        Move the drone to a specified position
        in the global GPS coordinate system with a given yaw angle.

        Parameters:
            pos (list or tuple):
                Position vector [latitude, longitude, altitude] where:
                    - latitude (float): Latitude in degrees.
                    - longitude (float): Longitude in degrees.
                    - altitude (float): Altitude in meters above
                                        mean sea level (AMSL).
            yaw (float):
                Yaw angle in degrees (0 = North, positive = clockwise).

        Returns:
            None:
                Sends the global position setpoint
                and waits for the drone to reach the target.
        """
        try:
            # Ensure the drone is in offboard mode
            await self._ensure_offboard_mode()

            # Create a global position setpoint
            position_setpoint = PositionGlobalYaw(
                lat_deg=pos[0], lon_deg=pos[1], alt_m=pos[2], yaw_deg=yaw, is_msl=True)

            # Send the global position setpoint to the drone
            await self.drone.offboard.set_position_global(position_setpoint)
            print(
                f"Commanded drone to move to position (lat: {pos[0]}, lon: {pos[1]}, alt: {pos[2]}) with yaw {yaw} degrees...")

            # Monitor the drone's position to confirm it has reached the target
            async for state in self.drone.telemetry.position():
                if (
                    abs(state.latitude_deg - pos[0]) < 0.00001 and
                    abs(state.longitude_deg - pos[1]) < 0.00001 and
                    abs(state.absolute_altitude_m - pos[2]) < 0.5
                ):
                    print("-- Drone reached target global position")
                    break
                await asyncio.sleep(0.1)

        except OffboardError as error:
            print(f"Offboard mode error: {error}")
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error in mov_to_lat_lon_alt: {e}")
            await self.drone.offboard.stop()

    async def mov_by_xyz(self, pos, yaw):
        """
        Move the drone by a relative displacement
        in the NED coordinate system with a given yaw angle.

        Parameters:
            pos (list or tuple):
                Relative position vector [x, y, z] in meters where:
                    - x (float): Displacement in meters along the North axis.
                    - y (float): Displacement in meters along the East axis.
                    - z (float): Displacement in meters along the Down axis
                        (positive down).
            yaw (float):
                Yaw angle in degrees (0 = North, positive = clockwise).

        Returns:
            None: Calculates the target position relative to the current
                  position, sends the position setpoint,
                  and waits for the drone to reach the target.
        """
        try:
            # Ensure the drone is in offboard mode
            await self._ensure_offboard_mode()

            # Get the current position in the local NED frame
            current_pos = await self.get_position_xyz()
            if current_pos is None:
                raise Exception("Failed to get current position")
            current_north, current_east, current_down = current_pos[0], current_pos[1], current_pos[2]
            # TODO: reuse already implemented functions

            # Calculate the target position by adding the relative displacement
            target_north = current_north + pos[0]
            target_east = current_east + pos[1]
            target_down = current_down + pos[2]

            # Create a position setpoint in NED coordinates
            position_setpoint = PositionNedYaw(
                north_m=target_north, east_m=target_east, down_m=target_down, yaw_deg=yaw)

            # Send the position setpoint to the drone
            await self.drone.offboard.set_position_ned(position_setpoint)
            print(
                f"Commanded drone to move by ({pos[0]}, {pos[1]}, {pos[2]}) to position ({target_north}, {target_east}, {target_down}) with yaw {yaw} degrees...")

            # Monitor the drone's position to confirm it has reached the target
            async for state in self.drone.telemetry.position_velocity_ned():
                if (
                    abs(state.position.north_m - target_north) < 0.5 and
                    abs(state.position.east_m - target_east) < 0.5 and
                    abs(state.position.down_m - target_down) < 0.5
                ):
                    print("-- Drone reached target position")
                    break
                await asyncio.sleep(0.1)

        except OffboardError as error:
            print(f"Offboard mode error: {error}")
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error in mov_by_xyz: {e}")
            await self.drone.offboard.stop()

    async def mov_with_speed(self, speed, yaw):
        """
        Move the drone with a specified speed in the direction defined
        by the yaw angle, maintaining the current altitude in the NED
        coordinate system.

        Parameters:
            speed (float):
                Speed in meters per second (magnitude of horizontal velocity).
            yaw (float):
                Yaw angle in degrees (0 = North, positive = clockwise),
                defining the direction of motion.

        Returns:
            None:
                Sends velocity setpoints to control the drone's motion
                in the horizontal plane until stopped.
        """
        try:
            # Ensure the drone is in offboard mode
            await self._ensure_offboard_mode()

            # Convert yaw angle from degrees to radians
            yaw_rad = math.radians(yaw)

            # Calculate velocity components in NED frame
            vx = speed * math.cos(yaw_rad)
            vy = speed * math.sin(yaw_rad)
            vz = 0.0

            # Create a velocity setpoint in NED coordinates
            velocity_setpoint = VelocityNedYaw(
                north_m_s=vx, east_m_s=vy, down_m_s=vz, yaw_deg=yaw)

            # Send the velocity setpoint to the drone
            await self.drone.offboard.set_velocity_ned(velocity_setpoint)
            print(
                f"Commanded drone to move with speed {speed} m/s in direction of yaw {yaw} degrees (vx: {vx}, vy: {vy}, vz: {vz})...")

            # Send the setpoint for a short duration (5 seconds)
            duration = 5
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < duration:
                await self.drone.offboard.set_velocity_ned(velocity_setpoint)
                await asyncio.sleep(0.1)

            # TODO: check logic against mission computer
            # probably only set no checks and no resets

            # Stop the drone by setting velocity to zero
            zero_velocity = VelocityNedYaw(0.0, 0.0, 0.0, yaw)
            await self.drone.offboard.set_velocity_ned(zero_velocity)
            print("-- Velocity setpoint set to zero; drone should hover or stop")

        except OffboardError as error:
            print(f"Offboard mode error: {error}")
            await self.drone.offboard.stop()
        except Exception as e:
            print(f"Error in mov_with_speed: {e}")
            await self.drone.offboard.stop()

    async def get_position_xyz(self):
        """
        Retrieve the drone's current position in the NED coordinate system.

        Returns:
            list: [x, y, z, roll, pitch, yaw] where:
                - x (float): Position in meters along the North axis.
                - y (float): Position in meters along the East axis.
                - z (float):
                    Position in meters along the Down axis (positive down).
                - roll (float): Roll angle in degrees.
                - pitch (float): Pitch angle in degrees.
                - yaw (float):
                    Yaw angle in degrees (0 = North, positive = clockwise).
        """
        try:
            # Fetch position data from telemetry in NED frame
            # Confirmed: position_velocity_ned provides NED coordinates (north_m, east_m, down_m)
            async for state in self.drone.telemetry.position_velocity_ned():
                position_data = state.position
                x = position_data.north_m
                y = position_data.east_m
                z = position_data.down_m
                break

            # Fetch attitude data
            attitude = await self._get_attitude()
            if attitude is None:
                return None
            roll, pitch, yaw = attitude

            return [x, y, z, roll, pitch, yaw]

        except Exception as e:
            print(f"Error in get_position_xyz: {e}")
            return None

    async def get_position_lat_lon_alt(self):
        """
        Retrieve the drone's current position in the GPS coordinate system.

        Returns:
            list: [lat, lon, alt, roll, pitch, yaw] where:
                - lat (float): Latitude in degrees.
                - lon (float): Longitude in degrees.
                - alt (float): Altitude in meters above mean sea level (AMSL).
                - roll (float): Roll angle in degrees.
                - pitch (float): Pitch angle in degrees.
                - yaw (float):
                    Yaw angle in degrees (0 = North, positive = clockwise).
        """
        try:
            # Fetch GPS position data
            async for state in self.drone.telemetry.position():
                lat = state.latitude_deg
                lon = state.longitude_deg
                alt = state.absolute_altitude_m
                break

            # Fetch attitude data
            attitude = await self._get_attitude()
            if attitude is None:
                return None
            roll, pitch, yaw = attitude

            return [lat, lon, alt, roll, pitch, yaw]

        except Exception as e:
            print(f"Error in get_position_lat_lon_alt: {e}")
            return None

    async def get_velocity_xyz(self):
        """
        Retrieve the drone's current velocity (vx, vy, vz)
        in the NED coordinate system.

        Returns:
            list: [vx, vy, vz, roll, pitch, yaw] where:
                - vx (float): Velocity in meters/second along the North axis.
                - vy (float): Velocity in meters/second along the East axis.
                - vz (float):
                    Velocity in meters/second along the Down axis
                    (positive down).
                - roll (float): Roll angle in degrees.
                - pitch (float): Pitch angle in degrees.
                - yaw (float):
                    Yaw angle in degrees (0 = North, positive = clockwise).
        """
        try:
            # Fetch velocity data
            async for state in self.drone.telemetry.position_velocity_ned():
                velocity_data = state.velocity
                vx = velocity_data.north_m_s
                vy = velocity_data.east_m_s
                vz = velocity_data.down_m_s
                break

            # Fetch attitude data
            attitude = await self._get_attitude()
            if attitude is None:
                return None
            roll, pitch, yaw = attitude

            return [vx, vy, vz, roll, pitch, yaw]

        except Exception as e:
            print(f"Error in get_velocity_xyz: {e}")
            return None

    async def send_status(self, status: str) -> bool:
        """
        Send a status message to the ground control station
        (e.g., QGroundControl).

        Parameters:
            status (str): The status message to send.

        Returns:
            bool:
                True if the status message was sent successfully,
                False otherwise.
        """
        try:
            if not self.drone:
                print("Error: No connection established")
                return False

            if not isinstance(status, str) or not status.strip():
                print("Error: Invalid or empty status message")
                return False

            if len(status) > 255:
                status = status[:255]
                print("Warning: Status message truncated to 255 characters")

            await self.drone.action.set_statustext(status)
            print(f"Status message sent: {status}")
            return True

        except Exception as e:
            print(f"Error in send_status: {e}")
            return False

    # TODO: check if needed with _get_relative_altitude
    async def get_relative_height(self):
        """
        Retrieve the drone's altitude above ground level in meters.

        Returns:
            float: Altitude above ground level in meters, or None if telemetry fails.
        """
        try:
            # Check if telemetry is healthy
            if not await self._check_telemetry_health():
                return None

            # Fetch relative altitude and vertical velocity
            relative_altitude = await self._get_relative_altitude()
            vertical_velocity = await self._get_vertical_velocity()

            if relative_altitude >= 0:
                # Here, we assume relative_altitude is reliable unless velocity suggests drift
                print(
                    f"AGL = {relative_altitude} meters (relative altitude, assuming flat terrain)")
                return relative_altitude
            else:
                print("Invalid relative altitude (negative)")
                return 0

        except Exception as e:
            print(f"Error in get_relative_height: {e}")
            return 0

    def send_image(self, image):
        """

        parms:
         image: Image Message

        return:
         ok: bool
        """
        # over WiFi
        pass

    def send_found_obj(self, obj):
        """

        parms:
         obj: Object Database

        return:
         ok: bool
        """
        pass

    def receive_mission_plan(self):
        """

        return:
         plan: str<json>
         ok: bool
        """
        # Over WiFi?
        # TODO: check what mission expects?
        pass
