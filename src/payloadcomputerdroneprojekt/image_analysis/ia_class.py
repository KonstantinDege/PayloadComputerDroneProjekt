import asyncio
import cv2
import numpy as np
from numpy.linalg import norm
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from payloadcomputerdroneprojekt.camera.abstract_class import AbstractCamera
from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis.data_handler import DataHandler
from payloadcomputerdroneprojekt.image_analysis.data_item import DataItem
import payloadcomputerdroneprojekt.image_analysis.math_helper as mh
from payloadcomputerdroneprojekt.helper import smart_print as sp
import time


class ImageAnalysis:
    """
    Handles image analysis for drone payload computer, including color and
    shape detection, object localization, and image quality assessment.

    :param config: Configuration dictionary for image analysis parameters.
    :type config: dict
    :param camera: Camera object implementing AbstractCamera.
    :type camera: AbstractCamera
    :param comms: Communications object for drone telemetry.
    :type comms: Communications
    """

    def __init__(
        self,
        config: dict,
        camera: AbstractCamera,
        comms: Communications
    ) -> None:
        """
        Initialize the ImageAnalysis object.

        :param config: Configuration dictionary.
        :type config: dict
        :param camera: Camera object.
        :type camera: AbstractCamera
        :param comms: Communications object.
        :type comms: Communications
        """
        self._detected_objects: list = []
        self.config: dict = config
        self._camera: AbstractCamera = camera
        self._comms: Communications = comms
        self._task: Optional[asyncio.Task] = None
        self._data_handler: DataHandler = DataHandler(config.setdefault(
            "path", "data/images"))

        def convert_to_lab(val: list) -> np.ndarray:
            """
            Convert color value from 0-100/0-255/0-255 to LAB color space.

            :param val: List of color values.
            :type val: list
            :return: Converted numpy array.
            :rtype: np.array
            """
            return np.array([val[0] * 2.55, val[1] + 128, val[2] + 128])
        self.colors: Dict[str, Union[Dict[str, np.ndarray],
                                     List[Dict[str, np.ndarray]]]] = {}
        for color in config["colors"]:
            if "upper_1" in color.keys():
                self.colors[color["name"]] = [
                    {
                        "lower": convert_to_lab(color["lower_0"]),
                        "upper": convert_to_lab(color["upper_0"])
                    },
                    {
                        "lower": convert_to_lab(color["lower_1"]),
                        "upper": convert_to_lab(color["upper_1"])
                    }
                ]
            else:
                self.colors[color["name"]] = {
                    "lower": convert_to_lab(color["lower"]),
                    "upper": convert_to_lab(color["upper"])
                }

        self.shape_color: Dict[str, np.ndarray] = {
            "lower": convert_to_lab(config["shape_color"]["lower"]),
            "upper": convert_to_lab(config["shape_color"]["upper"])
        }

        self.shape_funcs: Dict[str, Callable[..., List[dict]]] = {
            "Code": self._get_closest_code
        }

    def start_cam(self, images_per_second: float = 1.0) -> bool:
        """
        Start capturing and saving images asynchronously.

        :param images_per_second: Images per second (frames per second).
        :type images_per_second: float
        :return: True if camera started successfully, False otherwise.
        :rtype: bool
        """
        self._camera.start_camera()
        try:
            sp(f"starting camera with {images_per_second}")
            self._task = asyncio.create_task(
                self._async_analysis(images_per_second))
            return True
        except Exception as e:
            sp(f"Error starting the capture: {e}")
            return False

    def stop_cam(self) -> bool:
        """
        Stop capturing and saving images.

        :return: True if stopped successfully, False otherwise.
        :rtype: bool
        """
        try:
            self._task.cancel()
            return True
        except Exception as e:
            sp(f"Error stopping the capture: {e}")
            return False

    async def take_image(self) -> bool:
        """
        Take a single image asynchronously.

        :return: True if successful, False otherwise.
        :rtype: bool
        """
        try:
            await self._take_image()
        except Exception as e:
            sp(f"Take image failed {e}")
            return False
        return True

    async def _take_image(self) -> None:
        """
        Internal coroutine to take a single image and process it.

        :return: None
        """
        if not self._camera.is_active:
            self._camera.start_camera()
            await asyncio.sleep(2)
        await self.image_loop()

    async def _async_analysis(self, images_per_second: float) -> None:
        """
        Asynchronous loop to capture and process images at a given rate.

        :param images_per_second: Images per second.
        :type images_per_second: float
        :return: None
        """
        try:
            images_per_second = float(images_per_second)
        except Exception as e:
            sp("Could not convert images_per_second to float, "
               f"using Standard images_per_second=1; {e}")
            images_per_second = 1.0
        interval: float = 1.0 / images_per_second
        image_count: int = 0

        try:
            while True:
                sp(f"Current amount of images: {image_count}")
                image_count += 1
                try:
                    await self.image_loop()
                except Exception as e:
                    sp(f"Error {e} on Image with count: {image_count}")
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            sp("Capturing stopped.")

    async def image_loop(self) -> None:
        """
        Main logic for per-frame image analysis.

        :return: None
        """
        start_time: float = time.time()
        image: np.ndarray = self._camera.get_current_frame()
        position_data: List[Any] = await self._comms.get_position_lat_lon_alt()
        if start_time - time.time() < 0.25:
            self._image_sub_routine(image, position_data, position_data[2])
        else:
            sp("skipped image")

    def _image_sub_routine(
        self,
        image: np.ndarray,
        position_data: List[Any],
        height: float
    ) -> None:
        """
        Process a single image: save, check quality, detect objects, and
        annotate.

        :param image: Image array.
        :type image: np.array
        :param position_data: Position (lat, lon, alt, ...).
        :type position_data: list
        :param height: Height value.
        :type height: float
        :return: None
        """
        with self._data_handler as item:
            item.add_image_position(position_data)
            item.add_raw_image(image)
            item.add_height(height)
            if (quality := self.quality_of_image(
                    image)) < self.config.get("threashold", -1):
                sp("Skipped Image; Quality to low")
                item.add_quality(quality)
                return
            if position_data[0] == 0:
                return
            objects, shape_image = self.compute_image(image, item, height)
            item.add_objects(objects)

            loc_to_global: Callable[[float, float], Any] = mh.local_to_global(
                position_data[0], position_data[1])

            for obj in objects:
                obj["shape"] = self.get_shape(obj, shape_image, height)
                self.add_lat_lon(
                    obj, position_data[3:6], height, shape_image.shape[:2],
                    loc_to_global)
                cv2.circle(
                    image, (obj["x_center"], obj["y_center"]),
                    5, (166, 0, 178), -1)
                bounding_box = obj["bound_box"]
                cv2.rectangle(image,
                              (bounding_box["x_start"],
                               bounding_box["y_start"]),
                              (bounding_box["x_stop"],
                               bounding_box["y_stop"]), (0, 255, 0), 2)

            if self.config.get("save_shape_image", False):
                item.add_computed_image(image)
                item.add_image(shape_image, "shape")

    def compute_image(self, image: np.ndarray, item: Optional[DataItem] = None,
                      height: float = 1) -> Tuple[List[dict], np.ndarray]:
        """
        Filter image for defined colors and detect objects.

        :param image: Input image.
        :type image: np.array
        :return: Tuple of (list of detected objects, shape-filtered image).
        :rtype: tuple[list[dict], np.array]
        """
        objects: List[dict] = []
        filtered_images, shape_image = self.filter_colors(image)
        for filtered_image in filtered_images:
            self.detect_obj(objects, filtered_image, height=height)
            if item is not None and self.config.get("save_shape_image", False):
                item.add_image(filtered_image["filtered_image"],
                               filtered_image["color"])
        return objects, shape_image

    def detect_obj(
        self,
        objects: List[dict],
        filtered_image: Dict[str, Any],
        height: float = 1
    ) -> None:
        """
        Detect objects in a filtered image and append to objects list.

        :param objects: List to append detected objects.
        :type objects: list[dict]
        :param filtered_image: Dictionary with color and filtered image.
        :type filtered_image: dict
        :param height: Minimum height for object detection.
        :type height: float
        :return: None
        """
        if height <= 0:
            height = 0.01

        gray: np.ndarray = filtered_image["filtered_image"]

        contours, _ = cv2.findContours(
            gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            epsilon = self.config.get("approx_poly_epsilon", 0.04
                                      ) * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            x, y, w, h = cv2.boundingRect(approx)
            if (w**2 + h**2) < (self.config.get("min_diagonal", 10) / height
                                )**2:
                continue
            x_center = x + (w // 2)
            y_center = y + (h // 2)

            if self.config.get("strong_bounding_check", False):
                if len(approx) != 4:
                    continue
            else:
                if len(approx) > 16:
                    continue
            objects.append({
                "color": filtered_image["color"],
                "bound_box": {
                    "x_start": x,
                    "x_stop": x+w,
                    "y_start": y,
                    "y_stop": y+h
                },
                "x_center": x_center,
                "y_center": y_center
            })
            if len(approx) == 4:
                objects[-1]["contour"] = [[int(coord)
                                           for coord in pt[0]]
                                          for pt in approx]

    def _get_shrunk_subframe(self, bounding_box: dict,
                             image: np.ndarray) -> np.ndarray:
        """
        Get a subframe of the image, shrunk by a configurable percentage.
        :param bounding_box: Bounding box dictionary.
        :type bounding_box: dict
        :param image: Input image.
        :type image: np.array
        :return: Subframe of the image.
        :rtype: np.array
        """
        shrink_percent = self.config.get(
            "bounding_box_shrink_percentage", 0)
        x_start = bounding_box["x_start"]
        x_stop = bounding_box["x_stop"]
        y_start = bounding_box["y_start"]
        y_stop = bounding_box["y_stop"]
        w = x_stop - x_start
        h = y_stop - y_start
        dx = int(w * shrink_percent / 2)
        dy = int(h * shrink_percent / 2)
        x_start_shrunk = x_start + dx
        x_stop_shrunk = x_stop - dx
        y_start_shrunk = y_start + dy
        y_stop_shrunk = y_stop - dy
        return image[y_start_shrunk:y_stop_shrunk,
                     x_start_shrunk:x_stop_shrunk], \
            x_start_shrunk, y_start_shrunk

    def get_shape(
        self,
        obj: dict,
        shape_image: np.ndarray,
        height: float = 1
    ) -> Union[str, bool]:
        """
        Detect the shape inside the object boundaries.

        :param obj: Object dictionary.
        :type obj: dict
        :param shape_image: Shape-filtered image.
        :type shape_image: np.array
        :param height: Minimum height for shape detection.
        :type height: float
        :return: Shape name ("Dreieck", "Rechteck", "Kreis") or False.
        :rtype: str or bool
        """
        if height <= 0:
            height = 0.01

        bounding_box = obj["bound_box"]

        # Shrink bounding box by a configurable percentage (default 0%)
        gray, *_ = self._get_shrunk_subframe(bounding_box, shape_image)
        if gray.shape[0] < 5 or gray.shape[1] < 5:
            return False

        contours, _ = cv2.findContours(
            gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        possible_elements: List[Dict[str, Any]] = []
        rectangles: List[Dict[str, Any]] = []
        for contour in contours:
            epsilon = self.config.get("approx_poly_epsilon", 0.04
                                      ) * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            *_, w, h = cv2.boundingRect(approx)

            if (w**2 + h**2) < (self.config.get(
                    "min_diagonal_shape", 1) / height)**2:
                continue

            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0 or area < (
                    self.config.get("min_shape_area", 20) / height**2):
                continue

            if len(approx) == 3:
                possible_elements.append(
                    {"size": area, "shape": "Dreieck"})
            elif len(approx) > 4:
                possible_elements.append(
                    {"size": area, "shape": "Kreis"})
            elif len(approx) == 4:
                rectangles.append({"size": area, "shape": "Rechteck"})

        if len(possible_elements) == 0:
            possible_elements = rectangles

        if len(possible_elements) == 0:
            return False
        if len(possible_elements) == 1:
            return possible_elements[0]["shape"]
        # Sort by size and return the largest shape
        possible_elements = sorted(
            possible_elements, key=lambda x: x["size"], reverse=True)
        return possible_elements[0]["shape"]

    def find_code(
        self,
        obj: dict,
        shape_image: np.ndarray,
        height: float = 1
    ) -> bool:
        """
        Find code elements (e.g., QR code-like) inside the object.

        :param obj: Object dictionary.
        :type obj: dict
        :param shape_image: Shape-filtered image.
        :type shape_image: np.array
        :param height: Minimum height for code element detection.
        :type height: float
        :return: True if code found, False otherwise.
        :rtype: bool
        """
        if height <= 0:
            height = 0.01

        bounding_box = obj["bound_box"]

        subframe, x_start, y_start = self._get_shrunk_subframe(
            bounding_box, shape_image)
        if subframe.shape[0] < 5 or subframe.shape[1] < 5:
            return False

        contours, _ = cv2.findContours(
            subframe, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        code_elements: List[Dict[str, Any]] = []
        for contour in contours:
            epsilon = self.config.get("approx_poly_epsilon", 0.04
                                      ) * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            x, y, w, h = cv2.boundingRect(approx)
            if (w**2 + h**2) < (self.config.get("min_diagonal_code_element",
                                                1) / height)**2:
                continue
            if len(approx) == 4:
                code_elements.append(
                    {"x": x_start+x, "y": y_start+y,
                     "w": w, "h": h, "d": (w**2 + h**2)})

        if len(code_elements) < 3:
            return False
        if len(code_elements) == 3:
            obj["code"] = code_elements
        else:
            obj["code"] = sorted(
                code_elements, key=lambda x: x["d"], reverse=True)[:3]
        return True

    def filter_colors(
        self,
        image: np.ndarray
    ) -> Tuple[List[Dict[str, Any]], np.ndarray]:
        """
        Filter the image for each defined color and for the shape color.

        :param image: Input image.
        :type image: np.array
        :return: Tuple of (list of color-filtered dicts, shape-filtered image).
        :rtype: tuple[list[dict], np.array]
        """
        filtered_color_images: List[Dict[str, Any]] = []
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        shape_mask = self._filter_color(
            lab_image, self.shape_color)
        for name, elements in self.colors.items():
            filtered_color_images.append(
                {"color": name,
                 "filtered_image": self._filter_color(
                     lab_image, elements)})

        return filtered_color_images, shape_mask

    def filter_shape_color(self, image: np.ndarray) -> np.ndarray:
        """
        Filter the image for the shape color.

        :param image: Input image.
        :type image: np.array
        :return: Shape-filtered image.
        :rtype: np.array
        """
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        return self._filter_color(
            lab_image, self.shape_color)

    def filter_color(
        self,
        image: np.ndarray,
        color: str,
        shape_mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Filter the image for a specific color.

        :param image: Input image.
        :type image: np.array
        :param color: Color name (must be in defined colors).
        :type color: str
        :param shape_mask: Optional shape mask to apply.
        :type shape_mask: np.array or None
        :return: Filtered image.
        :rtype: np.array
        :raises IndexError: If color is not defined.
        """
        if color not in self.colors.keys():
            raise IndexError(
                f"the color {color} is not defined in the color list")
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        if shape_mask is not None:
            shape_mask = self._filter_color(
                lab_image, self.shape_color)
        return self._filter_color(lab_image, self.colors[color])

    def _filter_color(
        self,
        lab: np.ndarray,
        elements: Union[Dict[str, np.ndarray], List[Dict[str, np.ndarray]]],
    ) -> np.ndarray:
        """
        Internal method to filter an image in LAB color space for given color
        bounds.

        :param lab: LAB color image.
        :type lab: np.array
        :param elements: Color bounds (dict or list of dicts).
        :type elements: dict or list
        :param shape_mask: Optional shape mask.
        :type shape_mask: np.array or None
        :return: Filtered image.
        :rtype: np.array
        """
        if isinstance(elements, list):
            masks: List[np.ndarray] = []
            for elem in elements:
                masks.append(cv2.inRange(
                    lab, elem["lower"], elem["upper"]))

            mask = cv2.bitwise_or(masks[0], masks[1])
        else:
            mask = cv2.inRange(lab, elements["lower"], elements["upper"])

        blurred = cv2.GaussianBlur(mask, (15, 15), 0)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        denoised_mask = cv2.morphologyEx(blurred, cv2.MORPH_OPEN,
                                         kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        denoised_mask = cv2.morphologyEx(denoised_mask, cv2.MORPH_OPEN,
                                         kernel)

        denoised_mask = cv2.morphologyEx(denoised_mask, cv2.MORPH_CLOSE,
                                         kernel)

        blurred = cv2.GaussianBlur(mask, (7, 7), 0)

        _, thresh_mask = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh_mask

    async def get_current_offset_closest(
        self,
        color: str,
        shape: str,
        yaw_zero: bool = True,
        indoor: bool = False
    ) -> Tuple[Optional[List[float]], Optional[float], Optional[float]]:
        """
        Get the offset from the drone to the closest object of a given color
        and shape.

        :param color: Color name to detect.
        :type color: str
        :param shape: Shape name to detect.
        :type shape: str
        :param yaw_zero: If True, set yaw to zero for calculation.
        :type yaw_zero: bool
        :return: Tuple (offset [x, y], height, yaw offset).
        :rtype: tuple or (None, None, None) if not found
        """
        sp(self._camera.is_active)
        if not self._camera.is_active:
            self._camera.start_camera()
            await asyncio.sleep(2)
        with self._data_handler as item:
            position = await self._comms.get_position_xyz()
            if indoor:
                # For indoor use, height is negative of z coordinate
                relative_height = -1 * position[2]
            else:
                relative_height = await self._comms.get_relative_height()

            if relative_height <= 0:
                sp(f"Warning: detected_alt below 0 ({relative_height:.2f}),"
                   " clamping to 0")
                relative_height = 0.001

            image = self._camera.get_current_frame()
            item.add_image_position(position)
            item.add_raw_image(image)
            item.add_height(relative_height)
            return self._get_current_offset_closest(
                position, relative_height, image, color, shape, yaw_zero, item)

    def _get_current_offset_closest(
        self,
        position: List[float],
        relative_height: float,
        image: np.ndarray,
        color: str,
        shape: str,
        yaw_zero: bool = True,
        item: Optional[DataItem] = None
    ) -> Tuple[Optional[List[float]], Optional[float], Optional[float]]:
        """
        Internal method to get offset to closest object.

        :param position: Drone position (xyz).
        :type position: list[float]
        :param relative_height: Relative height.
        :type relative_height: float
        :param image: Image array.
        :type image: np.array
        :param color: Color name.
        :type color: str
        :param shape: Shape name.
        :type shape: str
        :param yaw_zero: If True, set yaw to zero.
        :type yaw_zero: bool
        :return: Tuple (offset [x, y], height, yaw offset).
        :rtype: tuple or (None, None, None) if not found
        """
        closest_obj = self.get_closest_element(image, color, shape, item,
                                               height=relative_height)
        if closest_obj is None:
            return None, None, None
        item.add_objects([closest_obj])
        if yaw_zero:
            position[5] = 0

        if "code" in closest_obj.keys():
            return self._get_height_estimate_yaw(
                closest_obj, position[3:6], relative_height, image.shape[:2])
        pos_out = self._get_height_estimate(
            closest_obj, position[3:6], relative_height, image.shape[:2])
        return [float(pos_out[0]), float(pos_out[1])], float(pos_out[2]), 0

    def _get_height_estimate_yaw(
        self,
        obj: dict,
        rotation: Union[List[float], np.ndarray],
        height_start: float,
        image_shape: Tuple[int, int]
    ) -> Tuple[List[float], float, float]:
        """
        Estimate height and yaw using code elements.

        :param obj: Object dictionary with code.
        :type obj: dict
        :param rotation: Rotation vector.
        :type rotation: list or np.array
        :param height_start: Initial height.
        :type height_start: float
        :param image_shape: Image shape.
        :type image_shape: tuple
        :return: Tuple ([x, y], height, yaw offset).
        :rtype: tuple
        """
        code_side_length = self.config.get("length_code_side", 0.5)
        height = height_start
        top_left, bottom_left, top_right = mh.find_relative_position(
            [(c["x"]+c["w"]/2, c["y"]+c["h"]/2, 0) for c in obj["code"]])
        for _ in range(5):
            top_left_pos = self._get_local_offset(
                top_left[:2], rotation, height, image_shape)
            bottom_left_pos = self._get_local_offset(
                bottom_left[:2], rotation, height, image_shape)
            top_right_pos = self._get_local_offset(
                top_right[:2], rotation, height, image_shape)

            left = norm(np.array(bottom_left_pos) - np.array(top_left_pos))
            top = norm(np.array(top_right_pos) - np.array(top_left_pos))

            height = height*(code_side_length/((left + top) / 2))

        top_left_pos = self._get_local_offset(
            top_left[:2], rotation, height, image_shape)
        bottom_left_pos = self._get_local_offset(
            bottom_left[:2], rotation, height, image_shape)
        top_right_pos = self._get_local_offset(
            top_right[:2], rotation, height, image_shape)

        left = norm(np.array(bottom_left_pos) - np.array(top_left_pos))
        top = norm(np.array(top_right_pos) - np.array(top_left_pos))

        pos = (bottom_left_pos + top_right_pos)[:2]

        obj["h"] = height

        return [float(pos[0]), float(pos[1])
                ], float(height), -mh.compute_rotation_angle(
                    top_left, bottom_left)

    def _get_height_estimate(
        self,
        obj: dict,
        rotation: Union[List[float], np.ndarray],
        height_start: float,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Estimate height using object contour and known box sizes.

        :param obj: Object dictionary.
        :type obj: dict
        :param rotation: Rotation vector.
        :type rotation: list or np.array
        :param height_start: Initial height.
        :type height_start: float
        :param image_shape: Image shape.
        :type image_shape: tuple
        :return: Local offset [x, y, z].
        :rtype: np.array
        """
        short_side_length = self.config.get("length_box_short_side", 0.4)
        long_side_length = self.config.get("length_box_long_side", 0.6)
        height = height_start

        for _ in range(3):
            points: List[np.ndarray] = []
            for point in obj["contour"]:
                points.append(self._get_local_offset(
                    point[:2], rotation, height, image_shape))
            short_sides, long_sides = mh.find_shortest_longest_sides(points)

            c = 0.0
            for s in short_sides:
                c += short_side_length/s

            for s in long_sides:
                c += long_side_length/s

            height = height*c/(len(short_sides)+len(long_sides))
        obj["h"] = height

        return self._get_local_offset(
            (obj["x_center"], obj["y_center"]), rotation, height, image_shape)

    def get_closest_element(
        self,
        image: np.ndarray,
        color: str,
        shape: Optional[str],
        item: Optional[DataItem] = None,
        height: float = 1
    ) -> Optional[dict]:
        """
        Get the closest detected object of a given color and shape.

        :param image: Input image.
        :type image: np.array
        :param color: Color name.
        :type color: str
        :param shape: Shape name.
        :type shape: str
        :return: Closest object dictionary or None.
        :rtype: dict or None
        """
        computed_image: Dict[str, Any] = {"color": color}
        shape_image = self.filter_shape_color(image)
        computed_image["filtered_image"] = self.filter_color(
            image, color, shape_image)
        item.add_computed_image(computed_image["filtered_image"])

        objects: List[dict] = []
        self.detect_obj(objects, computed_image, height=height)
        if shape is not None:
            if shape in self.shape_funcs:
                relevant_objects = self.shape_funcs["Code"](
                    objects, shape_image, shape, height)
            else:
                relevant_objects = self._get_correct_shape(
                    objects, shape_image, shape, height)
        else:
            relevant_objects = objects

        if len(relevant_objects) == 0:
            return None

        if len(relevant_objects) == 1:
            return relevant_objects[0]

        image_size = shape_image.shape[:2]

        def diag(obj: dict) -> float:
            return (obj["x_start"] - image_size[1]/2)**2 + \
                   (obj["y_start"] - image_size[1]/2)**2

        return sorted(relevant_objects, key=diag)[0]

    def _get_correct_shape(
        self,
        objects: List[dict],
        shape_image: np.ndarray,
        shape: str,
        height: float = 1
    ) -> List[dict]:
        """
        Filter objects by matching shape.

        :param objects: List of objects.
        :type objects: list
        :param shape_image: Shape-filtered image.
        :type shape_image: np.array
        :param shape: Shape name.
        :type shape: str
        :return: List of objects with matching shape.
        :rtype: list
        """
        relevant_objects: List[dict] = []
        for obj in objects:
            if self.get_shape(obj, shape_image, height) == shape:
                relevant_objects.append(obj)
        return relevant_objects

    def _get_closest_code(
        self,
        objects: List[dict],
        shape_image: np.ndarray,
        shape: str,
        height: float = 1
    ) -> List[dict]:
        """
        Filter objects by presence of code.

        :param objects: List of objects.
        :type objects: list
        :param shape_image: Shape-filtered image.
        :type shape_image: np.array
        :param shape: Shape name (unused).
        :type shape: str
        :return: List of objects with code detected.
        :rtype: list
        """
        relevant_objects: List[dict] = []
        for obj in objects:
            if self.find_code(obj, shape_image, height):
                relevant_objects.append(obj)
        return relevant_objects

    def get_filtered_objs(self) -> Dict[str, Dict[str, List[dict]]]:
        """
        Get a dictionary of all filtered objects.

        :return: Dictionary of filtered objects by color and shape.
        :rtype: dict[str, dict[str, list]]
        """
        return self._data_handler.get_filterd_items(
            self.config.get("distance_objs", 5))

    def get_matching_objects(
        self,
        color: str,
        shape: Optional[str] = None
    ) -> List[dict]:
        """
        Get all matching filtered objects for a color and optional shape.

        :param color: Color name.
        :type color: str
        :param shape: Shape name (optional).
        :type shape: str or None
        :return: List of object dictionaries.
        :rtype: list[dict]
        """
        return self.get_filtered_objs().get(color, {}).get(shape, [])

    def get_color_obj_list(self, color: str) -> List[dict]:
        """
        Get a list of all objects for a given color.

        :param color: Color name.
        :type color: str
        :return: List of object dictionaries.
        :rtype: list[dict]
        """
        out: List[dict] = []
        for shape, obj in self.get_filtered_objs().get(color, {}).items():
            obj["shape"] = shape
            out.append(obj)
        return out

    def get_all_obj_list(self) -> List[dict]:
        """
        Get a list of all detected objects with color and shape.

        :return: List of object dictionaries.
        :rtype: list[dict]
        """
        out: List[dict] = []
        for color, objs in self.get_filtered_objs().items():
            for shape, obj in objs.items():
                obj["color"] = color
                obj["shape"] = shape
                out.append(obj)
        return out

    @staticmethod
    def quality_of_image(image: np.ndarray) -> float:
        """
        Assess the quality of an image using Laplacian variance.

        :param image: Image array.
        :type image: np.array
        :return: Laplacian variance (higher is sharper).
        :rtype: float
        """
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        return laplacian.var()

    def get_local_offset(
        self,
        obj: dict,
        rotation: Union[List[float], np.ndarray],
        height: float,
        image_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Get the local offset of an object in the drone's coordinate system.

        :param obj: Object dictionary.
        :type obj: dict
        :param rotation: Rotation vector.
        :type rotation: list or np.array
        :param height: Height value.
        :type height: float
        :param image_size: Image size (height, width).
        :type image_size: tuple
        :return: Local offset [x, y, z].
        :rtype: np.array
        """
        if "contour" in obj.keys():
            return self._get_height_estimate(obj, rotation, height, image_size)
        return self._get_local_offset(
            (obj["x_center"], obj["y_center"]), rotation, height, image_size)

    def _get_local_offset(
        self,
        pixel: Tuple[int, int],
        rotation: Union[List[float], np.ndarray],
        height: float,
        image_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Internal method to compute local offset from pixel coordinates.

        :param pixel: Pixel coordinates (x, y).
        :type pixel: tuple
        :param rotation: Rotation vector.
        :type rotation: list or np.array
        :param height: Height value.
        :type height: float
        :param image_size: Image size (height, width).
        :type image_size: tuple
        :return: Local offset [x, y, z].
        :rtype: np.array
        """
        px, py = pixel
        rot_mat = mh.rotation_matrix(rotation)
        rotation = np.array(rotation) + \
            np.array(self.config.get("rotation_offset", [0, 0, 0]))

        fov = self.config.get("fov", [66, 41])  # shape is height width
        # offset of camera position in x and y compared to drone center
        camera_offset = np.array(self.config.get("camera_offset", [0, 0, 0]))
        local_vec = mh.compute_local(px, py, rotation, image_size, fov)

        local_vec_stretched = local_vec * height / local_vec[2]
        return local_vec_stretched + rot_mat @ camera_offset

    def add_lat_lon(
        self,
        obj: dict,
        rotation: Union[List[float], np.ndarray],
        height: float,
        image_size: Tuple[int, int],
        loc_to_global: Callable[[float, float], Any]
    ) -> None:
        """
        Add latitude and longitude to an object based on its local offset.

        :param obj: Object dictionary.
        :type obj: dict
        :param rotation: Rotation vector.
        :type rotation: list or np.array
        :param height: Height value.
        :type height: float
        :param image_size: Image size (height, width).
        :type image_size: tuple
        :param loc_to_global: Function to convert local to global coordinates.
        :type loc_to_global: callable
        :return: None
        """
        local_vec_stretched = self.get_local_offset(
            obj, rotation, height, image_size)

        obj["lat_lon"] = loc_to_global(
            local_vec_stretched[0], local_vec_stretched[1])[::-1]
