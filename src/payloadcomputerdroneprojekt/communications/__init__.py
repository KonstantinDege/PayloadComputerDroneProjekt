import asyncio
import math
from mavsdk import System
from mavsdk.offboard \
    import PositionNedYaw, PositionGlobalYaw, VelocityNedYaw, OffboardError


class Communications:
    def __init__(self, address):
        self.address = address
        self.drone = None

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
            async for health in self.drone.telemetry.health():
                if health.is_global_position_ok:
                    print("-- Drone is ready with valid GPS")
                    return True
                await asyncio.sleep(0.5)

            print("Warning: Connected but GPS not ready")
            return True

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
            async for state in self.drone.telemetry.health():
                if state.is_global_position_ok and state.is_home_position_ok:
                    print("-- Drone is connected and GPS is ready")
                    async for position in self.drone.telemetry.position():
                        self._home_lat = position.latitude_deg
                        self._home_lon = position.longitude_deg
                        self._home_alt = position.absolute_altitude_m
                        print(
                            f"Set NED origin at GPS: (lat: {self._home_lat}, "
                            f"lon: {self._home_lon}, alt: {self._home_alt})")
                        break
                    break
                else:
                    print(
                        "GPS unavailable, "
                        "proceeding without setting NED origin...")
                    break
                await asyncio.sleep(1)

            # Arm the drone
            print("Arming the drone...")
            await self.drone.action.arm()
            print("-- Drone armed successfully")
            # TODO: Wait until external arm

            # Set takeoff altitude (relative to ground)
            await self.drone.action.set_takeoff_altitude(altitude)
            print(f"Commanding takeoff to {altitude} meters...")

            # Command the drone to take off
            await self.drone.action.takeoff()

            # Wait until the drone reaches approximately the target altitude
            async for position in self.drone.telemetry.position():
                if abs(position.relative_altitude_m - altitude) < 0.5:
                    print(
                        "-- Drone reached target altitude "
                        f"of {altitude} meters")
                    break
                await asyncio.sleep(0.1)

            # Transition to offboard mode for hovering
            print("Switching to offboard mode...")
            await self.drone.offboard.set_position_ned(
                PositionNedYaw(0.0, 0.0, -altitude, 0.0))
            await self.drone.offboard.start()
            print("-- Offboard mode activated, drone is hovering")

            # TODO: function needs to end when hight reached
            # Continuously send position setpoints to maintain hover
            duration = 10
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < duration:
                await self.drone.offboard.set_position_ned(
                    PositionNedYaw(0.0, 0.0, -altitude, 0.0))
                await asyncio.sleep(0.1)

            print("-- Hover duration completed")

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
            None: Manages the descent, lands the drone, and disarms it.
        """
        try:
            # Get the current altitude to confirm starting position
            async for position in self.drone.telemetry.position():
                current_altitude = position.relative_altitude_m
                print(f"Current altitude: {current_altitude} meters")
                break

            # Transition to offboard mode for controlled descent
            print("Switching to offboard mode for controlled descent...")
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
            # TODO: check if is in offboard -> error
            await self.drone.offboard.start()
            print("-- Offboard mode activated")

            # Phase 1: Descend to 0.5 meters at a moderate speed (0.5 m/s)
            target_altitude = 0.5
            descent_speed = 0.5
            if current_altitude > target_altitude:
                print(
                    f"Descending to {target_altitude} meters "
                    f"at {descent_speed} m/s...")
                async for position in self.drone.telemetry.position():
                    await self.drone.offboard.set_velocity_ned(
                        VelocityNedYaw(0.0, 0.0, descent_speed, 0.0))
                    if position.relative_altitude_m <= target_altitude + 0.1:
                        print("-- Reached altitude 0.5 meters")
                        break
                    await asyncio.sleep(0.1)

            # Phase 2: Slow descent at 0.1 m/s for the final 0.5 meters
            slow_descent_speed = 0.1
            print(
                f"Descending final 0.5 meters at {slow_descent_speed} m/s...")
            async for position in self.drone.telemetry.position():
                await self.drone.offboard.set_velocity_ned(
                    VelocityNedYaw(0.0, 0.0, slow_descent_speed, 0.0))
                if position.relative_altitude_m <= 0.1:
                    print("Drone near ground, initiating final landing...")
                    break
                await asyncio.sleep(0.1)

            # TODO: when should disarm???, mission 3 only on last
            # stay in offboard

            # Stop offboard mode and command final landing
            await self.drone.offboard.stop()
            print("Offboard mode stopped, commanding landing...")
            await self.drone.action.land()

            # Wait for the drone to land and disarm
            async for state in self.drone.telemetry.in_air():
                if not state:
                    print("-- Drone has landed")
                    break
                await asyncio.sleep(0.1)

            # Disarm the drone
            print("Disarming the drone...")
            await self.drone.action.disarm()
            print("-- Drone disarmed successfully")

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
            if not await self.drone.offboard.is_active():
                await self.drone.offboard.start()
                print("-- Offboard mode activated")

            # Create a position setpoint in NED coordinates
            position_setpoint = PositionNedYaw(
                north_m=pos[0],
                east_m=pos[1],
                down_m=pos[2],
                yaw_deg=yaw
            )

            # Send the position setpoint to the drone
            await self.drone.offboard.set_position_ned(position_setpoint)
            print(
                f"Commanded drone to move to position ({pos[0]}, "
                f"{pos[1]}, {pos[2]}) with yaw {yaw} degrees...")

            # Monitor the drone's position to confirm it has reached the target
            async for state in self.drone.telemetry.position_velocity_ned():
                if (
                    abs(state.position.north_m - pos[0]) < 0.5 and
                    abs(state.position.east_m - pos[1]) < 0.5 and
                    abs(state.position.down_m - pos[2]) < 0.5
                ):
                    print("-- Drone reached target position")
                    break
                await asyncio.sleep(0.1)  # TODO: check if needed?

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
            if not await self.drone.offboard.is_active():
                await self.drone.offboard.start()
                print("-- Offboard mode activated")

            # Create a global position setpoint
            position_setpoint = PositionGlobalYaw(
                lat_deg=pos[0],
                lon_deg=pos[1],
                alt_m=pos[2],
                yaw_deg=yaw,
                is_msl=True
            )

            # Send the global position setpoint to the drone
            await self.drone.offboard.set_position_global(position_setpoint)
            print(
                "Commanded drone to move to position "
                f"(lat: {pos[0]}, lon: {pos[1]}, alt: {pos[2]}) "
                f"with yaw {yaw} degrees...")

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
            if not await self.drone.offboard.is_active():
                await self.drone.offboard.start()
                print("-- Offboard mode activated")

            # Get the current position in the local NED frame
            async for state in self.drone.telemetry.position_velocity_ned():
                current_pos = state.position
                current_north = current_pos.north_m
                current_east = current_pos.east_m
                current_down = current_pos.down_m
                break
            # TODO: reuse already implemented functions

            # Calculate the target position by adding the relative displacement
            target_north = current_north + pos[0]
            target_east = current_east + pos[1]
            target_down = current_down + pos[2]

            # Create a position setpoint in NED coordinates
            position_setpoint = PositionNedYaw(
                north_m=target_north,
                east_m=target_east,
                down_m=target_down,
                yaw_deg=yaw
            )

            # Send the position setpoint to the drone
            await self.drone.offboard.set_position_ned(position_setpoint)
            print(
                f"Commanded drone to move by ({pos[0]}, {pos[1]}, {pos[2]}) "
                f"to position ({target_north}, {target_east}, {target_down}) "
                f"with yaw {yaw} degrees...")

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
            if not await self.drone.offboard.is_active():
                await self.drone.offboard.start()
                print("-- Offboard mode activated")

            # Convert yaw angle from degrees to radians
            yaw_rad = math.radians(yaw)

            # Calculate velocity components in NED frame
            vx = speed * math.cos(yaw_rad)
            vy = speed * math.sin(yaw_rad)
            vz = 0.0

            # Create a velocity setpoint in NED coordinates
            velocity_setpoint = VelocityNedYaw(
                north_m_s=vx,
                east_m_s=vy,
                down_m_s=vz,
                yaw_deg=yaw
            )

            # Send the velocity setpoint to the drone
            await self.drone.offboard.set_velocity_ned(velocity_setpoint)
            print(
                f"Commanded drone to move with speed {speed} m/s "
                f"in direction of yaw {yaw} degrees (vx: {vx}, "
                f"vy: {vy}, vz: {vz})...")

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
            print(
                "-- Velocity setpoint set to zero; drone should hover or stop")

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
            # TODO: check if coordinate system is correct
            async for state in self.drone.telemetry.position_velocity_ned():
                position_data = state.position
                x = position_data.north_m
                y = position_data.east_m
                z = position_data.down_m
                break

            # Fetch attitude data
            async for attitude in self.drone.telemetry.attitude_euler():
                roll = attitude.roll_deg
                pitch = attitude.pitch_deg
                yaw = attitude.yaw_deg
                break

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
            async for attitude in self.drone.telemetry.attitude_euler():
                roll = attitude.roll_deg
                pitch = attitude.pitch_deg
                yaw = attitude.yaw_deg
                break

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
            async for attitude in self.drone.telemetry.attitude_euler():
                roll = attitude.roll_deg
                pitch = attitude.pitch_deg
                yaw = attitude.yaw_deg
                break

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

    def send_image(self, image):
        """

        parms:
         image: Image Message

        return:
         ok: bool
        """
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

        # TODO: check what mission expects?
        pass
