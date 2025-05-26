from payloadcomputerdroneprojekt.communications import Communications
import asyncio
import unittest

PORT = "udp://:14540"


class CommAsync:
    @staticmethod
    async def move_by():
        con = Communications(address=PORT, config={"allowed_arm": True})
        await con.connect()
        await con.start()
        print("start checkpoint")
        await con.mov_by_xyz([0, -15, 0])
        print("first checkpoint")
        await con.mov_to_xyz([0, 0, -5])
        await con.land()

    @staticmethod
    async def move_to_xyz():
        con = Communications(address=PORT, config={"allowed_arm": True})
        await con.connect()
        await con.start()
        print("start checkpoint")
        await con.mov_by_xyz([0, 0, -5], 90)
        await con.mov_by_xyz([0, -15, 0])
        print("first checkpoint")
        await con.land()

    @staticmethod
    async def move_by_xyz_old():
        con = Communications(address=PORT, config={"allowed_arm": True})
        await con.connect()
        await con.start()
        print("start checkpoint")
        await con.mov_by_xyz_old([0, 0, -5], 90)
        await con.mov_by_xyz_old([0, -15, 0])
        print("first checkpoint")
        await con.land()

    @staticmethod
    async def move_by_speed():
        con = Communications(address=PORT, config={"allowed_arm": True})
        await con.connect()
        await con.start()
        print("start checkpoint")
        await con.mov_by_vel([0, 0, -5], 90)
        print("first checkpoint1")
        await con.mov_by_vel([5, 0, 0])
        print("first checkpoint2")
        await asyncio.sleep(15)
        await con.land()

    @staticmethod
    async def move_with_speed():
        con = Communications(address=PORT, config={"allowed_arm": True})
        await con.connect()
        await con.start()
        print("start checkpoint")
        await con.mov_with_vel([0, 0, -5], 90)
        print("first checkpoint1")
        await con.mov_with_vel([5, 0, 0])
        print("first checkpoint2")
        await asyncio.sleep(15)
        await con.land()

    @staticmethod
    async def move_global():
        con = Communications(address=PORT, config={"allowed_arm": True})
        await con.connect()
        await con.start()
        pos = await con.get_position_lat_lon_alt()
        print(pos)
        await con.mov_to_lat_lon_alt(pos[:2] + [10])
        print("in global mode")
        await con.land()


class TestCommunication(unittest.TestCase):
    def test_move_by(self):
        asyncio.run(CommAsync.move_by())

    def test_move_by_rel_yaw(self):
        asyncio.run(CommAsync.move_to_xyz())

    def test_move_by_xyz_old(self):
        asyncio.run(CommAsync.move_by_xyz_old())

    def test_move_by_speed(self):
        asyncio.run(CommAsync.move_by_speed())

    def test_move_with_speed(self):
        asyncio.run(CommAsync.move_with_speed())

    def test_move_global_1(self):
        asyncio.run(CommAsync.move_global())


if __name__ == '__main__':
    unittest.main()
