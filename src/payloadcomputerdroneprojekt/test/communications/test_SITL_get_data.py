from payloadcomputerdroneprojekt.communications import Communications
import asyncio
import unittest

PORT = "udp://:14540"


class CommAsync:
    @staticmethod
    async def get_lat_lon_alt():
        con = Communications(address=PORT)
        await con.connect()
        pos = await con.get_position_lat_lon_alt()
        print(f"LatLonAlt {pos}")

    @staticmethod
    async def get_xyz():
        con = Communications(address=PORT)
        await con.connect()
        pos = await con.get_position_xyz()
        print(f"XYZ {pos}")

    @staticmethod
    async def get_height():
        con = Communications(address=PORT)
        await con.connect()
        pos = await con.get_relative_height()
        print(f"Height {pos}")

    @staticmethod
    async def is_flying():
        con = Communications(address=PORT)
        await con.connect()
        pos = await con.is_flying()
        print(f"In flight {pos}")


class TestCommunication(unittest.TestCase):
    def test_get_lat_lon_alt(self):
        asyncio.run(CommAsync.get_lat_lon_alt())

    def test_get_xyz(self):
        asyncio.run(CommAsync.get_xyz())

    def test_get_height(self):
        asyncio.run(CommAsync.get_height())

    def test_is_flighing(self):
        asyncio.run(CommAsync.is_flying())


if __name__ == '__main__':
    unittest.main()
