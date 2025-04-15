import payloadcomputerdroneprojekt.camera as cam
from payloadcomputerdroneprojekt.camera.gazebo_sitl.gazebo_camera_lib \
    import Video


class Camera(cam.Camera):
    def __init__(self):
        super().__init__()

    def start_camera(self):
        self._camera = Video()
        print("Camera started")

    def get_current_frame(self):
        while True:
            # Wait for the next frame
            if not self._camera.frame_available():
                continue
            return self._camera.frame()
