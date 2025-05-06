from payloadcomputerdroneprojekt.communications import Communications
import asyncio
import unittest

PORT = "udp://:14540"


class CommAsync:
    @staticmethod
    async def move_by():
        con = Communications(address=PORT)
        await con.connect()
        await con.start()
        print("start checkpoint")
        await con.mov_by_xyz([0, -5, 0], 0)
        print("first checkpoint")
        await con.mov_by_xyz([0, -5, 0], 0)


class TestCommunication(unittest.TestCase):
    def test_move_by(self):
        asyncio.run(CommAsync.move_by())


if __name__ == '__main__':
    unittest.main()
