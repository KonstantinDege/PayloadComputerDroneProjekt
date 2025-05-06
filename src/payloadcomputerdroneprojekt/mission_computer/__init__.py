from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import json
import asyncio


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
            self.current_mission_plan = json.load(file)

        self.mode = self.current_mission_plan["mode"]
        if self.mode == 1:
            asyncio.run(self._mission_1_find_and_count())
        elif self.mode == 2:
            asyncio.run(self._mission_2_find_and_land())
        elif self.mode == 3:
            asyncio.run(self._mission_3_land_and_repeat())
        else:
            print("Unbekannter Missionsmodus:", self.mode)

    async def _mission_1_find_and_count(self):

        print("Mission 1: Find and Count")

        await self._comms.start(object["height"])
        self._image.start_cam()

        for waypoint in object["waypoints"]:
            pos = waypoint["pos"]
            yaw = waypoint["yaw"]

            await self._comms.move_to_latlonal(pos, yaw)

        self._image.stop_cam()
        await self._comms.mov_to_latlonalt(object["land"], 0)
        self._comms.land()

        print("Mission 1 abgeschlossen.")

    async def _mission_2_find_and_land(self):

        print("Mission 2: Find and Land")

        """
        definition pos und yaw

        pos = input("Gib die Position in lat, lon, alt ein: ")
        pos = [lat, lon, alt]
        yaw = input("Gib die Yaw in yaw_x, yaw_y, yaw_z ein: ")
        yaw = [yaw_x, yaw_y, yaw_z]

        """

        self._comms.connect()
        self._image._camera.start_camera()

        self.land_at(self.current_mission_plan["objective"])

        print("Mission 2 abgeschlossen")

    async def _mission_3_land_and_repeat(self):
        print("Mission 3: Land and Repeat")

        self._comms.connect()
        self._image._camera.start_camera()

        for objective in self.current_mission_plan["objectives"]:
            await self.land_at(objective)

        print("Mission 3 abgeschlossen")


    async def land_at(self, objective):
        await self._comms.start(objective["height"])
        await self._comms.mov_to_latlonalt(objective["targetpos"], 0)

        offset, h = self._image.get_current_offset_closest(
            objective["color"], objective["type"])

        await self._comms.mov_by_xyz(offset[0], offset[1], 0)
        while True:
            offset, h = self._image.get_current_offset_closest(
                objective["color"], objective["type"])
            await self._comms.mov_by_xyz(offset[0], offset[1], 0)
            if abs(offset[0]) < 1 and abs(offset[1]) < 1:
                await self._comms.mov_by_xyz(0, 0, h-3)
                break

        while True:
            offset, h = self._image.get_current_offset_closest(
                objective["color"], objective["type"])
            await self._comms.mov_with_v(smooth(offset[0], offset[1], 0))
            if abs(offset[0]) < 0.05 and abs(offset[1]) < 0.05:
                await self._comms.mov_by_xyz(0, 0, h)
                break


def smooth(x, y, z):
    """
    smoothes the input values
    """
    return [x, y, z]
