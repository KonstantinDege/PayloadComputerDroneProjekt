import asyncio
import cv2
import numpy as np
from payloadcomputerdroneprojekt.camera import Camera
from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis.data_handler import DataHandler
import payloadcomputerdroneprojekt.image_analysis.math_helper as mh


class ImageAnalysis:
    def __init__(self, config: dict, camera: Camera, comms: Communications):
        self._obj = []
        self.config = config
        self._camera = camera
        self._comms = comms
        self._dh = DataHandler(config["path"])

        self.colors: dict = {}
        for color in config["colors"]:
            if "upper_1" in color.keys():
                self.colors[color["name"]] = [
                    {
                        "lower": np.array(color["lower_0"]),
                        "upper": np.array(color["upper_0"])
                    },
                    {
                        "lower": np.array(color["lower_1"]),
                        "upper": np.array(color["upper_1"])
                    }
                ]

            else:
                self.colors[color["name"]] = {
                    "lower": np.array(color["lower"]),
                    "upper": np.array(color["upper"])
                }

        self.shape_color = {
            "lower": np.array([config["shape_color"]["lower"]]),
            "upper": np.array([config["shape_color"]["upper"]])
        }

    async def async_analysis(self, ips: float):
        """
        finished
        What does the function do?
            Captures images and saves them at the given FPS rate.
        How is the function tested?
            Simulation
        How will the function work?
            See above.

        params:
            fps: Frames per second at which the camera should capture images
        """
        try:
            ips = float(ips)
        except Exception as e:
            print(f"Could not ips to float, using Standard ips=1; {e}")
            ips = 1.0

        interval = 1.0 / ips
        count = 0

        try:
            while True:
                try:
                    self.image_loop()
                except Exception as e:
                    print(f"Error {e} on Image with count: {count}")
                print(f"Current amount of images: {count}")
                count += 1
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            print("Capturing stopped.")

    def image_loop(self) -> None:
        image = self._camera.get_current_frame()
        pos, rot = self._comms.get_position_latlonalt()
        self._image_sub_routine(image, pos, rot)

    def _image_sub_routine(self, image, pos, rot):
        with self._dh as item:
            item.add_position(pos, rot)
            item.add_raw_image(image)
            if (quality := self.quality_of_image(
                    image)) < self.config["threashold"]:
                print("Skipped Image; Quality to low")
                return
            item.add_quality(quality)
            objects, shape_image = self.compute_image(image)
            # item.add_computed_image(computed_image)
            item.add_objects(objects)

            for obj in objects:
                obj["shape"] = self.get_shape(obj, shape_image)
                # TODO: add FOV to config
                mh.add_latlonalt(obj, pos, rot,
                                 imagesize=image.shape[:2], fov=(41, 66))

    def compute_image(self, image: np.array):
        objects: list[dict] = []
        filtered_images, shape_image = self.filter_colors(image)
        for filtered_image in filtered_images:
            self.detect_obj(filtered_image, objects)
        return objects, shape_image

    def detect_obj(self, filtered_image: np.array, objects: list[dict]):
        image = cv2.resize(
            filtered_image["filtered_image"], (0, 0), fx=0.3, fy=0.3)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.04 * cv2.arcLength(contour, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            if (w**2 + h**2) < self.config["min_diagonal"]**2:
                continue
            if len(approx) == 4:
                x_mittel = x + (w // 2)
                y_mittel = y + (h // 2)
            else:
                continue
            objects.append({
                "color": filtered_image["color"],
                "bound_box": {
                    "x_start": x,
                    "x_stop": x+w,
                    "y_start": y,
                    "y_stop": y+h
                },
                "x_center": x_mittel,
                "y_center": y_mittel
            })
        return objects

    def get_shape(self, obj: dict, shape_image: np.array):
        image = cv2.resize(shape_image, (0, 0), fx=0.3, fy=0.3)

        bound_box = obj["bound_box"]

        subframe = image[bound_box["y_start"]:bound_box["y_stop"],
                         bound_box["x_start"]:bound_box["x_stop"]]

        gray = cv2.cvtColor(subframe, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.04 * cv2.arcLength(contour, True), True)
            if len(approx) == 3:
                return "Dreieck"
            elif len(approx) == 4:
                return "Rechteck"
            elif len(approx) > 4:
                return "Kreis"

        return False

    def filter_colors(self, image: np.array):
        image_show = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        for name, elements in self.colors.items():

            image_show.append(
                {"color": name,
                 "filtered_image": self._filter_color(hsv, image, elements)})

        shape_image = self._filter_color(
            hsv, cv2.bitwise_not(image), self.shape_color)

        return image_show, shape_image

    def filter_color(self, image: np.array, color: str):
        return self._filter_color(cv2.cvtColor(image, cv2.COLOR_BGR2HSV),
                                  image, self.colors[color])

    def _filter_color(self, hsv, image, elements: dict):
        if isinstance(elements, list):
            masks = []
            for elem in elements:
                masks.append(cv2.inRange(
                    hsv, elem["lower"], elem["upper"]))

            mask = cv2.bitwise_or(masks[0], masks[1])
        else:
            mask = cv2.inRange(hsv, elements["lower"], elements["upper"])

        return cv2.bitwise_and(image, image, mask=mask)

    def start_cam(self, ips: float = 1.0) -> bool:
        """
        finished
        What does the function do?
            Starts capturing and saving images.
        How is the function tested?
            Simulation
        How will the function work?
            An asynchronous task is started to capture and save images,
            so the program flow is not interrupted.

        params:
            fps: Frames per second at which the camera should capture images
        return:
            success: bool
        """
        self._camera.start_camera()
        try:
            self._task = asyncio.create_task(self.async_analysis(ips))
            return True
        except Exception as e:
            print(f"Error starting the capture: {e}")
            return False

    def stop_cam(self) -> bool:
        """
        finished
        What does the function do?
            Stops capturing and saving images.
        How is the function tested?
            Simulation
        How will the function work?
            An asynchronous task is stopped.

        return:
            success: bool
        """
        try:
            self._task.cancel()
            return True
        except Exception as e:  # TODO: try finding correct Exception Type
            print(f"Error stopping the capture: {e}")
            return False

    def get_current_offset_closest(self, color, type_of_obj):
        """
        What does the function do?
            Returns the offset from the drone to the object.
        How is the function tested? simulation / unit tests
        How will the function work?
            The object is detected using object detection,
            and the offset is calculated using pixels and additional geometry.

        params:
            color: color which should be detected []
            type_of_obj: type of object (rectangle, circle, etc.) str
        return
         (x,y) correct to closest
         h height estimation
        """

        pass

    def get_filtered_objs(self):
        object_store: dict[str, dict] = {}
        for items in self._dh.get_items():
            for obj in items["found_objs"]:
                d = object_store.setdefault(obj["color"], {})
                if obj.get("shape", False):
                    d.setdefault(obj["shape"], []).append(obj)
                else:
                    d.setdefault("all", []).append(obj)

        # TODO: add sorting for distance for each shape, and add all to each of
        # those runs so that all elements under deltapos < same_obj_distance
        # are in one list
        print(object_store)

    @staticmethod
    def quality_of_image(image: np.array):  # finished
        """
        finished
        capture false input
        What does the function do?
            Checks the quality of the image to determine
            if it is suitable for evaluation.
        How is the function tested?
            Unit tests
        How will the function work?
            The Laplace variance is calculated,
            and if it is below a certain value,
            the image is classified as blurry/unusable.

        parms:
         image: Image array
        return:
         variance: float
        """

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()
