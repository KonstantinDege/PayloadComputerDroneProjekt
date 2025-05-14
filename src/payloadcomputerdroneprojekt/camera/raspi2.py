import payloadcomputerdroneprojekt.camera as cam
from picamera2 import Picamera2


class RaspiCamera(cam.Camera):
    def __init__(self, config):
        super().__init__(config)
        self._camera = Picamera2()
        if not self._config:
            self._config = {"format": 'XRGB8888', "size": (640, 480)}
        self._config["size"] = tuple(self._config["size"])

    def start_camera(self, config=None):
        if self.is_active:
            if config:
                self._config = config
                self.stop_camera()
                self.start_camera()
            return
        config = self._camera.create_preview_configuration(
            main=self._config
        )
        self._camera.align_configuration(config)
        self._camera.configure(config)
        self._camera.start()
        self.is_active = True
        print("Camera started")

    def get_current_frame(self):
        return self._camera.capture_array()

    def stop_camera(self):
        self._camera.stop()
        self.is_active = False


if __name__ == "__main__":
    cam = RaspiCamera(None)
    cam.start_camera()
    cam.get_current_frame()
