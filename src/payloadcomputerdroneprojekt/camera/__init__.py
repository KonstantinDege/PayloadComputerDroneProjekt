from abc import ABC, abstractmethod


class Camera(ABC):
    def __init__(self):
        super().__init__()
        self._camera = None

    @abstractmethod
    def start_camera(self):
        pass

    @abstractmethod
    def get_current_frame(self):
        pass
