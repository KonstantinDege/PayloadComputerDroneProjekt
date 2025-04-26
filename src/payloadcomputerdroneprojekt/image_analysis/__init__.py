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
                        "lower": np.array(color["lower"]),
                        "upper": np.array(color["upper"])
                    },
                    {
                        "lower": np.array(color["lower"]),
                        "upper": np.array(color["upper"])
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
        pos, rot = self._comms.get_position_latlonalt()
        image = self._camera.get_current_frame()
        if quality := self.quality_of_image(
                image) < self.config["treashold"]:
            return

        with self._dh as item:
            item.add_position(pos, rot)
            item.add_raw_image(image)
            item.add_quality(quality)
            objects, computed_image, shape_image = self.compute_image(image)
            # item.add_computed_image(computed_image)
            item.add_objects(objects)
            for obj in objects:
                obj["shape"] = self.get_shape(obj, shape_image)
                mh.add_latlonalt(obj, pos, rot)

    def compute_image(self, image: np.array):
        objects: list[dict] = []
        filtered_images, computed_image, shape_image = \
            self.filter_colors(image)
        for filtered_image in filtered_images:
            self.detect_obj(filtered_image, objects)
        return objects, computed_image, shape_image

    def detect_obj(self, filtered_image: np.array, objects: list[dict]):
        image = cv2.resize(
            filtered_image["filtered image"], (0, 0), fx=0.3, fy=0.3)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.04 * cv2.arcLength(contour, True), True)
            x, y, w, h = cv2.boundingRect(approx)
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

    def get_shape(self, black_image: np.array, obj: dict):
        image = cv2.resize(black_image, (0, 0), fx=0.3, fy=0.3)
        bound_box = obj["bound_box"]
        subframe = image[bound_box["x_start"]:bound_box["x_stop"],
                         bound_box["y_start"]:bound_box["y_stop"]]

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
                return "Kreis oder Ellipse"
            else:
                return False

    def filter_colors(self, image: np.array):
        image_show = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        for name, elements in self.colors:
            # red has two ranges in hsv
            if isinstance(elements, list):
                masks = []
                for elem in elements:
                    masks.append(cv2.inRange(
                        hsv, elem["lower"], elem["upper"]))

                mask = cv2.bitwise_or(**masks)
            else:
                mask = cv2.inRange(hsv, elements["lower"], elements["upper"])

            filtered_image = cv2.bitwise_and(image, image, mask=mask)
            image_show.append(
                {"color": name, "filtered image": filtered_image})

        mask = cv2.inRange(
            hsv, self.shape_color["lower"],  self.shape_color["upper"])
        shape_image = cv2.bitwise_and(image, image, mask=mask)

        return image_show, shape_image

    def filter_color(self, image: np.array, color: str):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        elements = self.colors[color]
        if isinstance(elements, list):
            masks = []
            for elem in elements:
                masks.append(cv2.inRange(
                    hsv, elem["lower"], elem["upper"]))

            mask = cv2.bitwise_or(**masks)
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
        variance = laplacian.var()
        return variance
