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


class TestCommunication(unittest.TestCase):
    def test_move_by(self):
        asyncio.run(CommAsync.move_by())


if __name__ == '__main__':
    unittest.main()
