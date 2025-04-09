class Communications:
    def __init__(self, commlink):
        self.mavsdk = commlink

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

    def mov_v(self, v, yaw):
        """
        parms:
         v: Velocity Vector
         yaw: Yaw Angle
        """
        pass

    def get_position(self):
        """

        return [x,y,z,roll,pitch,yaw]
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
