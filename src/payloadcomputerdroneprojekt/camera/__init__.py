from abc import ABC, abstractmethod


class Camera(ABC):
    def __init__(self, config):
        super().__init__()
        self._config = config
        self._camera = None

    @abstractmethod
    def start_camera(self):
        pass

    @abstractmethod
    def get_current_frame(self):
        pass
