import payloadcomputerdroneprojekt.camera.abstract_class as cam
from payloadcomputerdroneprojekt.camera.gazebo_sitl.gazebo_camera_lib \
    import Video


class GazeboCamera(cam.AbstractCamera):
    def __init__(self, config):
        super().__init__(config)

    def start_camera(self, config=None):
        self._camera = Video(self._config.get("port", 5600))
        print("Camera started")

    def get_current_frame(self):
        while True:
            # Wait for the next frame
            if not self._camera.frame_available():
                continue
            return self._camera.frame()

    def stop_camera(self):
        pass
