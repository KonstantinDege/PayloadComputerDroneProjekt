from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import json


class MissionComputer():

    """
    this function starts the computer

    see "Ablaufdiagramm.png"

    parms:
        missionfile: file descriping the mission and it's parameters
                    if not given waiting for Network
    """

    def __init__(self, camera, port, communications=Communications, image_analysis=ImageAnalysis):
        self._comms = communications(port)
        self._image = image_analysis(camera, self._comms)

        self.current_mission_plan = {}

    def start(self, missionfile=""):
        with open(missionfile, "r") as file:
            self.mission_plan = json.load(file)

        self.mode = self.mission_plan["mode"]
        if self.mode == 1:
            self._mission_1_find_and_count()
        elif self.mode == 2:
            self._mission_2_find_and_land()
        elif self.mode == 3:
            self._mission_3_land_and_repeat()
        else:
            print("Unbekannter Missionsmodus:", self.mode)

    async def _mission_1_find_and_count(self):

        print("Mission 1: Find and Count")

        await self._comms.start(self.mission_plan["height"])
        self._image.start_cam()

        for waypoint in self.mission_plan["waypoints"]:
            pos = waypoint["pos"]
            yaw = waypoint["yaw"]

            await self._comms.move_to_latlonal(pos, yaw)

        self._image.stop_cam()
        await self._comms.mov_to_latlonalt(self.mission_plan["land"], 0)
        self._comms.land()

        print("Mission 1 abgeschlossen.")

    def _mission_2_find_and_land(self):

        print("Mission 2: Find and Land")

        """
        definition pos und yaw

        pos = input("Gib die Position in lat, lon, alt ein: ")
        pos = [lat, lon, alt]
        yaw = input("Gib die Yaw in yaw_x, yaw_y, yaw_z ein: ")
        yaw = [yaw_x, yaw_y, yaw_z]

        """

        self._comms.start(15)
        self._image.start_async_camera()
        self._comms.move_to_latlonal(pos, yaw)
        self._image.get_current_offset_closest(color, typ)

        print("Mission 2 abgeschlossen")

    def _mission_3_land_and_repeat(self):

        print("Mission 3: Land and Repeat")

        """
        definition pos und yaw

        pos = input("Gib die Position in lat, lon, alt ein: ")
        pos = [lat, lon, alt]
        yaw = input("Gib die Yaw in yaw_x, yaw_y, yaw_z ein: ")
        yaw = [yaw_x, yaw_y, yaw_z]

        """
        self._comms.connect()
        self._image.start()
        self._comms.start(15)
        self._comms.move_to_latlonal(pos, yaw)
        self._image.get_current_offset(color, pos)

        print("Mission 3 abgeschlossen")
        pass
