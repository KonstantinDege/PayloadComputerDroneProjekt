import payloadcomputerdroneprojekt.camera as cam
from picamera2 import Picamera2


class RaspiCamera(cam.Camera):
    def __init__(self, config):
        super().__init__(config)
        if not self._config:
            self._config = {"format": 'XRGB8888', "size": (640, 480)}
        self._config["size"] = tuple(self._config["size"])

    def start_camera(self):
        self._camera = Picamera2()
        self._camera.configure(
            self._camera.create_preview_configuration(
                main=self._config
            ))
        self._camera.start()
        print("Camera started")

    def get_current_frame(self):
        return self._camera.capture_array()


if __name__ == "__main__":
    cam = RaspiCamera(None)
    cam.start_camera()
    cam.get_current_frame()
