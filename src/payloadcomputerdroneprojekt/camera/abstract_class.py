from abc import ABC, abstractmethod


class AbstractCamera(ABC):
    """
    Abstract base class for camera implementations.
    This class defines the interface for camera operations such as starting,
    capturing frames, and stopping the camera.
    """
    def __init__(self, config):
        super().__init__()
        self._config = config
        self._camera = None
        self.is_active = False

    @abstractmethod
    def start_camera(self, config=None):
        """
        Start the camera with the given configuration.
        :param config: Optional configuration for the camera.
        """
        pass

    @abstractmethod
    def get_current_frame(self):
        """
        Capture the current frame from the camera.
        :return: The captured frame.
        """
        pass

    @abstractmethod
    def stop_camera(self):
        """
        Stop the camera.
        """
        pass
