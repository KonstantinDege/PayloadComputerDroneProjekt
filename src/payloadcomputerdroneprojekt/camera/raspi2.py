import payloadcomputerdroneprojekt.camera.abstract_class as cam
from picamera2 import Picamera2
from libcamera import Transform


class RaspiCamera(cam.AbstractCamera):
    def __init__(self, config):
        super().__init__(config)
        if not self._config:
            self._config = {"main": {"format": 'XRGB8888', "size": (640, 480)}}
        self._config["main"]["size"] = tuple(self._config["main"]["size"])

    def start_camera(self, config=None):
        if self.is_active:
            if config:
                self._config = config
                self._config["main"][
                    "size"] = tuple(self._config["main"]["size"])
                self.stop_camera()
                self.start_camera()
            return

        self._camera = Picamera2()
        self.mode = self._camera.sensor_modes[0]
        self._camera.configure(
            self._camera.create_video_configuration(
                main=self._config["main"],
                sensor={'output_size': self.mode['size'],
                        'bit_depth': self.mode['bit_depth']},
                transform=Transform(hflip=1, vflip=1))
        )
        self._camera.set_controls(
            self._config.get("control", {"ExposureTime": 50}))

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
