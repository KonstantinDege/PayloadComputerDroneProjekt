from abc import ABC, abstractmethod


class Camera(ABC):
    def __init__(self, config):
        super().__init__()
        self._config = config
        self._camera = None
        self.is_active = False

    @abstractmethod
    def start_camera(self, config=None):
        pass

    @abstractmethod
    def get_current_frame(self):
        pass

    @abstractmethod
    def stop_camera(self):
        pass
