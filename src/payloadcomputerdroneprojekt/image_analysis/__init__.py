import asyncio
import cv2
import numpy as np
from payloadcomputerdroneprojekt.camera import Camera
from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis.data_handler import DataHandler
import payloadcomputerdroneprojekt.image_analysis.math_helper as mh
import tempfile


class ImageAnalysis:
    def __init__(self, config: dict, camera: Camera, comms: Communications):
        self._obj = []
        self.config = config
        self._camera = camera
        self._comms = comms
        self._dh = DataHandler(config.setdefault(
            "path", tempfile.mkdtemp(prefix="image_analysis")))

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
            self._task = asyncio.create_task(self._async_analysis(ips))
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

    async def _async_analysis(self, ips: float):
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
                print(f"Current amount of images: {count}")
                count += 1
                try:
                    await self.image_loop()
                except Exception as e:
                    print(f"Error {e} on Image with count: {count}")
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            print("Capturing stopped.")

    async def image_loop(self) -> None:
        """
        Wraps the logik that runs the analysis each frame.
        """
        image = self._camera.get_current_frame()
        pos_com = await self._comms.get_position_lat_lon_alt()
        height = await self._comms.get_relative_height()
        self._image_sub_routine(image, pos_com, height)

    def _image_sub_routine(self, image, pos_com, height):
        with self._dh as item:
            item.add_image_position(pos_com)
            item.add_raw_image(image)
            item.add_height(height)
            if (quality := self.quality_of_image(
                    image)) < self.config["threashold"]:
                print("Skipped Image; Quality to low")
                return
            item.add_quality(quality)
            objects, shape_image = self.compute_image(image)
            item.add_objects(objects)

            for obj in objects:
                obj["shape"] = self.get_shape(obj, shape_image)
                # TODO: add FOV to config
                self.add_latlonalt(obj, pos_com, height, shape_image.shape[:2])
                # cv2.circle(
                #     image, (obj["x_center"], obj["y_center"]),
                #     2, (166, 0, 178), -1)

            cv2.circle(
                image, (350, 10),
                2, (166, 0, 178), -1)

            item.add_computed_image(image)

    def compute_image(self, image: np.array) -> tuple[list[dict], np.array]:
        """
        Filters image for colors and returns all found color squares and a
        total image filtered for shape color.

        Args:
            image (np.array): Image to filter for colors

        Returns:
            objects (list[dict]):
                Returns a list of dict that contains all information of each
                obj
            shape_image (np.array):
                A image filtered for the shape color
        """
        objects: list[dict] = []
        filtered_images, shape_image = self.filter_colors(image)
        for filtered_image in filtered_images:
            self.detect_obj(objects, filtered_image)
        return objects, shape_image

    def detect_obj(self, objects: list[dict],
                   filtered_image: np.array) -> None:
        """_summary_

        Args:
            objects (list[dict]): List to append new obj
            filtered_image (np.array): color filtered image

        Returns:
            None
        """
        gray = cv2.cvtColor(
            filtered_image["filtered_image"], cv2.COLOR_BGR2GRAY)
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
                "contour": [[int(y) for y in x[0]] for x in approx],
                "x_center": x_mittel,
                "y_center": y_mittel
            })

    def get_shape(self, obj: dict, shape_image: np.array):
        """
        Returns the first plossible shape that is inside the object boundaries

        Args:
            obj (dict): info dict of one object
            shape_image (np.array):

        Returns:
            str: The shape name inside
        """
        bound_box = obj["bound_box"]

        subframe = shape_image[bound_box["y_start"]:bound_box["y_stop"],
                               bound_box["x_start"]:bound_box["x_stop"]]

        gray = cv2.cvtColor(subframe, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.04 * cv2.arcLength(contour, True), True)
            *_, w, h = cv2.boundingRect(approx)
            if (w**2 + h**2) < self.config.get("min_diagonal_shape", 1)**2:
                continue
            if len(approx) == 3:
                return "Dreieck"
            elif len(approx) == 4:
                return "Rechteck"
            elif len(approx) > 4:
                return "Kreis"

        return False

    def filter_colors(self, image: np.array) -> tuple[list[dict], np.array]:
        """
        Filters the Image for each of the defined colors

        Args:
            image (np.array):

        Returns:
            image_show: list of dict that contain color name and filtered image
            shape_image: image filtered for shape_color (f.E. black or white)
        """
        image_show = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        for name, elements in self.colors.items():
            image_show.append(
                {"color": name,
                 "filtered_image": self._filter_color(hsv, image, elements)})

        shape_image = self._filter_color(
            hsv, image, self.shape_color, invert=True)

        return image_show, shape_image

    def filter_color(self, image: np.array, color: str) -> np.array:
        """
        Returns the image filtered for the specified color.

        Args:
            image (np.array): _description_
            color (str): Color name needs to be in the list of defined colors

        Returns:
            np.array: filtered image
        """
        if color not in self.colors.keys():
            raise IndexError(
                f"the color {color} is not defined in the color list")
        return self._filter_color(cv2.cvtColor(image, cv2.COLOR_BGR2HSV),
                                  image, self.colors[color])

    def _filter_color(self, hsv, image, elements: dict, invert: bool = False):
        if isinstance(elements, list):
            masks = []
            for elem in elements:
                masks.append(cv2.inRange(
                    hsv, elem["lower"], elem["upper"]))

            mask = cv2.bitwise_or(masks[0], masks[1])
        else:
            mask = cv2.inRange(hsv, elements["lower"], elements["upper"])

        if invert:
            image = cv2.bitwise_not(image)
            return cv2.bitwise_and(image, image, mask=mask)
        else:
            return cv2.bitwise_and(image, image, mask=mask)

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

    def get_filtered_objs(self) -> list[dict]:
        """
        Returns a list of all filtered obj

        Returns:
            dict[str, dict[str, list]]: _description_
        """
        object_store = self._get_obj_tree()

        # TODO: add sorting for distance for each shape, and add all to each of
        # those runs so that all elements under deltapos < same_obj_distance
        # are in one list
        print(object_store)

    def get_matching_objects(self, color: str, shape: str = None
                             ) -> list[dict]:
        """
        Returns all matching filtered objects

        Args:
            color (str): name of the color
            shape (str, optional): name of the shape. Defaults to None.

        Returns:
            list[dict]: Obj dictionaries
        """

    def _get_obj_tree(self) -> dict[str, dict[str, list[dict]]]:
        object_store: dict[str, dict] = {}
        for items in self._dh.get_items():
            for obj in items["found_objs"]:
                d = object_store.setdefault(obj["color"], {})
                if obj.get("shape", False):
                    d.setdefault(obj["shape"], []).append(obj)
                else:
                    d.setdefault("all", []).append(obj)
        return object_store

    @staticmethod
    def quality_of_image(image: np.array) -> float:  # finished
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

    def add_latlonalt(self, obj, pos_com, height, imagesize):
        px, py = obj["x_center"], obj["y_center"]
        pos, rot = pos_com[0:3], pos_com[3:6]
        rot = np.array(rot) + \
            np.array(self.config.get("rotation_offset", [0, 0, 0]))

        fov = self.config.get("fov", [66, 41])  # shape is height width
        # offset of camera position in x and y compared to drone center
        offset = np.array(self.config.get("camera_offset", [0, 0, 0]))
        local_vec = mh.compute_local(px, py, rot, offset, imagesize, fov)

        local_vec_streched = local_vec * height / local_vec[2]

        obj["latlonalt"] = []
        return local_vec_streched
