import payloadcomputerdroneprojekt.camera.abstract_class as cam
from picamera2 import Picamera2
from libcamera import Transform


class RaspiCamera(cam.AbstractCamera):
    def __init__(self, config):
        super().__init__(config)
        if not self._config:
            self._config = {
                "main": {"format": 'RGB888', "size": (1920, 1080)}}
            # old default 640x480
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

        tuning = Picamera2.load_tuning_file("imx708.json")
        self._camera = Picamera2(tuning=tuning)
        self.mode = self._camera.sensor_modes[0]
        self._camera.configure(
            self._camera.create_preview_configuration(
                main=self._config["main"],
                transform=Transform(hflip=1, vflip=1))
        )
        self._camera.set_controls(
            # old default 50
            self._config.get("control", {"ExposureTime": 1500}))

        self._camera.start()
        self.is_active = True
        print("Camera started")

    def get_current_frame(self):
        return self._camera.capture_array()

    def stop_camera(self):
        self._camera.stop()
        self.is_active = False


if __name__ == "__main__":
    import json
    with open("start_scripts/config_px4.json", "r") as f:
        j = json.load(f)["camera"]
    cam = RaspiCamera(j)
    cam.start_camera()
    import cv2
    i = cam.get_current_frame()
    cv2.imwrite("test.jpg", i)
