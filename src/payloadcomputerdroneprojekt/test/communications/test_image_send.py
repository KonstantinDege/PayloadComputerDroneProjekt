from payloadcomputerdroneprojekt.communications import Communications
import asyncio
import unittest
import os

PORT = "udp://:14540"


class CommAsync:
    @staticmethod
    async def send_image():
        # Configure for localhost testing in WSL
        config = {
            "laptop_ip": "127.0.0.1",
            "laptop_port": 5000,
            "network_timeout": 10
        }
        con = Communications(address=PORT, config=config)
        try:
            await con.connect()
        except Exception as e:
            print(f"Connect failed (non-fatal for send_image): {e}")
        # Ensure test image exists
        test_image = "test.jpg"
        if not os.path.isfile(test_image):
            raise FileNotFoundError(f"Test image not found: {test_image}")
        print("Starting image send")
        result = await con.send_image(test_image)
        print("Image send checkpoint")
        return result


class TestCommunication(unittest.TestCase):
    def test_send_image(self):
        result = asyncio.run(CommAsync.send_image())
        self.assertTrue(result, "Failed to send image")


if __name__ == '__main__':
    unittest.main()
