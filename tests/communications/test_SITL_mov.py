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
        await con.mov_by_xyz([0, 0, -10], 0)


class TestCommunication(unittest.TestCase):
    def test_move_by(self):
        asyncio.run(CommAsync.move_by())


if __name__ == '__main__':
    unittest.main()
