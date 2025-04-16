import asyncio
from mavsdk import System


class Communications:
    def __init__(self, address):
        self._address = address

    def connect(self):
        # check if it should be refactored
        self._connection = System()
        asyncio.run(self._connection.connect(system_address=self._address))
        print("MavSDK established")

    def start(self, h):
        pass

    def land(self):
        pass

    def mov_to_xyz(self, pos, yaw):
        """
        parms:
         pos: Postition Vector local
         yaw: Yaw Angle
        """
        pass

    def mov_to_latlonalt(self, pos, yaw):
        """
        parms:
         pos: Postition Vector global
         yaw: Yaw Angle
        """
        pass

    def mov_by_xyz(self, pos, yaw):
        """
        parms:
         pos: Postition Vector local relativ
         yaw: Yaw Angle
        """
        pass

    def mov_with_v(self, v, yaw):
        """
        parms:
         v: Velocity Vector
         yaw: Yaw Angle
        """
        pass

    def get_position_xyz(self):
        """

        return [x,y,z,roll,pitch,yaw]
        """
        pass

    def get_position_latlonalt(self):
        """

        return [lat,lon,alt,roll,pitch,yaw]
        """
        pass

    def get_velocity_xyz(self):
        """

        return [x,y,z,roll,pitch,yaw]
        """
        pass

    def send_precision_land(delta_pos):
        """
        parms:
         pos: Postition Vector local relativ
         yaw: Yaw Angle
        """
        pass

    def send_status(self, status: str):
        """

        parms:
         status: Status Message

        return:
         ok: bool
        """
        pass

    def send_image(self, image):
        """

        parms:
         image: Image Message

        return:
         ok: bool
        """
        pass

    def send_found_obj(self):
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
        pass
