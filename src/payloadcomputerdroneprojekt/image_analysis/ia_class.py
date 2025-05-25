import asyncio
import cv2
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from payloadcomputerdroneprojekt.camera.abstract_class import AbstractCamera
from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis.data_handler import DataHandler
import payloadcomputerdroneprojekt.image_analysis.math_helper as mh
import tempfile
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
        self._obj: list = []
        self.config: dict = config
        self._camera: AbstractCamera = camera
        self._comms: Communications = comms
        self._task: Optional[asyncio.Task] = None
        self._dh: DataHandler = DataHandler(config.setdefault(
            "path", tempfile.mkdtemp(prefix="image_analysis")))

        def conhsv(val: list) -> np.ndarray:
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
                        "lower": conhsv(color["lower_0"]),
                        "upper": conhsv(color["upper_0"])
                    },
                    {
                        "lower": conhsv(color["lower_1"]),
                        "upper": conhsv(color["upper_1"])
                    }
                ]
            else:
                self.colors[color["name"]] = {
                    "lower": conhsv(color["lower"]),
                    "upper": conhsv(color["upper"])
                }

        self.shape_color: Dict[str, np.ndarray] = {
            "lower": conhsv(config["shape_color"]["lower"]),
            "upper": conhsv(config["shape_color"]["upper"])
        }

        self.shape_funcs: Dict[str, Callable[..., List[dict]]] = {
            "Code": self._get_closest_code
        }

    def start_cam(self, ips: float = 1.0) -> bool:
        """
        Start capturing and saving images asynchronously.

        :param ips: Images per second (frames per second).
        :type ips: float
        :return: True if camera started successfully, False otherwise.
        :rtype: bool
        """
        self._camera.start_camera()
        try:
            sp(f"starting camera with {ips}")
            self._task = asyncio.create_task(self._async_analysis(ips))
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

    async def _async_analysis(self, ips: float) -> None:
        """
        Asynchronous loop to capture and process images at a given rate.

        :param ips: Images per second.
        :type ips: float
        :return: None
        """
        try:
            ips = float(ips)
        except Exception as e:
            sp(f"Could not convert ips to float, using Standard ips=1; {e}")
            ips = 1.0
        interval: float = 1.0 / ips
        count: int = 0

        try:
            while True:
                sp(f"Current amount of images: {count}")
                count += 1
                try:
                    await self.image_loop()
                except Exception as e:
                    sp(f"Error {e} on Image with count: {count}")
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            sp("Capturing stopped.")

    async def image_loop(self) -> None:
        """
        Main logic for per-frame image analysis.

        :return: None
        """
        st: float = time.time()
        image: np.ndarray = self._camera.get_current_frame()
        pos_com: List[Any] = await self._comms.get_position_lat_lon_alt()
        if st - time.time() < 0.25:
            self._image_sub_routine(image, pos_com, pos_com[2])
        else:
            sp("skipped image")

    def _image_sub_routine(
        self,
        image: np.ndarray,
        pos_com: List[Any],
        height: float
    ) -> None:
        """
        Process a single image: save, check quality, detect objects, and
        annotate.

        :param image: Image array.
        :type image: np.array
        :param pos_com: Position (lat, lon, alt, ...).
        :type pos_com: list
        :param height: Height value.
        :type height: float
        :return: None
        """
        with self._dh as item:
            item.add_image_position(pos_com)
            item.add_raw_image(image)
            item.add_height(height)
            if (quality := self.quality_of_image(
                    image)) < self.config.get("threashold", -1):
                sp("Skipped Image; Quality to low")
                item.add_quality(quality)
                return
            if pos_com[0] == 0:
                return
            objects, shape_image = self.compute_image(image)
            item.add_objects(objects)

            loc_to_glo: Callable[[float, float], Any] = mh.local_to_global(
                pos_com[0], pos_com[1])

            for obj in objects:
                obj["shape"] = self.get_shape(obj, shape_image)
                self.add_lat_lon(
                    obj, pos_com[3:6], height, shape_image.shape[:2],
                    loc_to_glo)
                cv2.circle(
                    image, (obj["x_center"], obj["y_center"]),
                    5, (166, 0, 178), -1)
                bb = obj["bound_box"]
                cv2.rectangle(image, (bb["x_start"], bb["y_start"]),
                              (bb["x_stop"], bb["y_stop"]), (0, 255, 0), 2)

            item.add_computed_image(image)

    def compute_image(self, image: np.ndarray
                      ) -> Tuple[List[dict], np.ndarray]:
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
            self.detect_obj(objects, filtered_image)
        return objects, shape_image

    def detect_obj(
        self,
        objects: List[dict],
        filtered_image: Dict[str, Any]
    ) -> None:
        """
        Detect objects in a filtered image and append to objects list.

        :param objects: List to append detected objects.
        :type objects: list[dict]
        :param filtered_image: Dictionary with color and filtered image.
        :type filtered_image: dict
        :return: None
        """
        gray: np.ndarray = filtered_image["filtered_image"]
        blurred: np.ndarray = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.04 * cv2.arcLength(contour, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            if (w**2 + h**2) < self.config.get("min_diagonal", 10)**2:
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

    def get_shape(
        self,
        obj: dict,
        shape_image: np.ndarray
    ) -> Union[str, bool]:
        """
        Detect the shape inside the object boundaries.

        :param obj: Object dictionary.
        :type obj: dict
        :param shape_image: Shape-filtered image.
        :type shape_image: np.array
        :return: Shape name ("Dreieck", "Rechteck", "Kreis") or False.
        :rtype: str or bool
        """
        bound_box = obj["bound_box"]

        subframe = shape_image[bound_box["y_start"]:bound_box["y_stop"],
                               bound_box["x_start"]:bound_box["x_stop"]]

        gray = subframe
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

    def find_code(
        self,
        obj: dict,
        shape_image: np.ndarray
    ) -> bool:
        """
        Find code elements (e.g., QR code-like) inside the object.

        :param obj: Object dictionary.
        :type obj: dict
        :param shape_image: Shape-filtered image.
        :type shape_image: np.array
        :return: True if code found, False otherwise.
        :rtype: bool
        """
        bound_box = obj["bound_box"]

        subframe = shape_image[bound_box["y_start"]:bound_box["y_stop"],
                               bound_box["x_start"]:bound_box["x_stop"]]

        gray = subframe
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        code_elements: List[Dict[str, Any]] = []
        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.04 * cv2.arcLength(contour, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            if (w**2 + h**2) < self.config.get(
                    "min_diagonal_code_element", 1)**2:
                continue
            if len(approx) == 4:
                code_elements.append(
                    {"x": x, "y": y, "w": w, "h": h, "d": (w**2 + h**2)})

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
        image_show: List[Dict[str, Any]] = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        shape_mask = self._filter_color(
            hsv, self.shape_color)
        for name, elements in self.colors.items():
            image_show.append(
                {"color": name,
                 "filtered_image": self._filter_color(
                     hsv, elements, shape_mask=shape_mask)})

        return image_show, shape_mask

    def filter_shape_color(self, image: np.ndarray) -> np.ndarray:
        """
        Filter the image for the shape color.

        :param image: Input image.
        :type image: np.array
        :return: Shape-filtered image.
        :rtype: np.array
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        return self._filter_color(
            hsv, self.shape_color)

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
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        if shape_mask is not None:
            shape_mask = self._filter_color(
                hsv, self.shape_color)
        return self._filter_color(hsv, self.colors[color],
                                  shape_mask=shape_mask)

    def _filter_color(
        self,
        lab: np.ndarray,
        elements: Union[Dict[str, np.ndarray], List[Dict[str, np.ndarray]]],
        shape_mask: Optional[np.ndarray] = None
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

        if shape_mask is None:
            return cv2.GaussianBlur(mask, (5, 5), 0)

        # mask = cv2.bitwise_or(mask, shape_mask)
        return cv2.GaussianBlur(mask, (7, 7), 0)

    async def get_current_offset_closest(
        self,
        color: str,
        shape: str,
        yaw_0: bool = True
    ) -> Tuple[Optional[List[float]], Optional[float], Optional[float]]:
        """
        Get the offset from the drone to the closest object of a given color
        and shape.

        :param color: Color name to detect.
        :type color: str
        :param shape: Shape name to detect.
        :type shape: str
        :param yaw_0: If True, set yaw to zero for calculation.
        :type yaw_0: bool
        :return: Tuple (offset [x, y], height, yaw offset).
        :rtype: tuple or (None, None, None) if not found
        """
        if not self._camera.is_active:
            self._camera.start_camera()
            await asyncio.sleep(2)
        pos = self._comms.get_position_xyz()
        dh = self._comms.get_relative_height()
        img = self._camera.get_current_frame()
        return self._get_current_offset_closest(
            pos, dh, img, color, shape, yaw_0)

    def _get_current_offset_closest(
        self,
        pos: List[float],
        dh: float,
        img: np.ndarray,
        color: str,
        shape: str,
        yaw_0: bool = True
    ) -> Tuple[Optional[List[float]], Optional[float], Optional[float]]:
        """
        Internal method to get offset to closest object.

        :param pos: Drone position (xyz).
        :type pos: list[float]
        :param dh: Relative height.
        :type dh: float
        :param img: Image array.
        :type img: np.array
        :param color: Color name.
        :type color: str
        :param shape: Shape name.
        :type shape: str
        :param yaw_0: If True, set yaw to zero.
        :type yaw_0: bool
        :return: Tuple (offset [x, y], height, yaw offset).
        :rtype: tuple or (None, None, None) if not found
        """
        closest_obj = self.get_closest_element(img, color, shape)
        if closest_obj is None:
            return None, None, None

        if yaw_0:
            pos[5] = 0

        if "code" in closest_obj.keys():
            return self._get_height_estimate_yaw(
                closest_obj, pos[3:6], dh, img.shape[:2])
        pos_out = self._get_height_estimate(
            closest_obj, pos[3:6], dh, img.shape[:2])
        return [float(pos_out[0]), float(pos_out[1])], float(pos_out[2]), 0

    def _get_height_estimate_yaw(
        self,
        obj: dict,
        rot: Union[List[float], np.ndarray],
        h_start: float,
        shape: Tuple[int, int]
    ) -> Tuple[List[float], float, float]:
        """
        Estimate height and yaw using code elements.

        :param obj: Object dictionary with code.
        :type obj: dict
        :param rot: Rotation vector.
        :type rot: list or np.array
        :param h_start: Initial height.
        :type h_start: float
        :param shape: Image shape.
        :type shape: tuple
        :return: Tuple ([x, y], height, yaw offset).
        :rtype: tuple
        """
        al = self.config.get("length_code_side", 0.5)
        h = h_start
        t_l, b_l, t_r = mh.find_rel_position(
            [(c["x"]+c["w"]/2, c["y"]+c["h"]/2, 0) for c in obj["code"]])
        for _ in range(5):
            t_l_pos = self._get_local_offset(t_l[:2], rot, h, shape)
            b_l_pos = self._get_local_offset(b_l[:2], rot, h, shape)
            t_r_pos = self._get_local_offset(t_r[:2], rot, h, shape)

            left = np.linalg.norm(np.array(b_l_pos) - np.array(t_l_pos))
            top = np.linalg.norm(np.array(t_r_pos) - np.array(t_l_pos))
            h = h*(al*(1/left + 1/top) / 2)

        t_l_pos = self._get_local_offset(t_l[:2], rot, h, shape)
        b_l_pos = self._get_local_offset(b_l[:2], rot, h, shape)
        t_r_pos = self._get_local_offset(t_r[:2], rot, h, shape)

        left = np.linalg.norm(np.array(b_l_pos) - np.array(t_l_pos))
        top = np.linalg.norm(np.array(t_r_pos) - np.array(t_l_pos))
        pos = (b_l_pos + t_r_pos)[:2]

        obj["h"] = h

        return [float(pos[0]), float(pos[1])
                ], float(h), -mh.compute_rotation_angle(t_l, b_l)

    def _get_height_estimate(
        self,
        obj: dict,
        rot: Union[List[float], np.ndarray],
        h_start: float,
        shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Estimate height using object contour and known box sizes.

        :param obj: Object dictionary.
        :type obj: dict
        :param rot: Rotation vector.
        :type rot: list or np.array
        :param h_start: Initial height.
        :type h_start: float
        :param shape: Image shape.
        :type shape: tuple
        :return: Local offset [x, y, z].
        :rtype: np.array
        """
        als = self.config.get("length_box_short_side", 0.4)
        all = self.config.get("length_box_long_side", 0.6)
        h = h_start

        for _ in range(3):
            points: List[np.ndarray] = []
            for o in obj["contour"]:
                points.append(self._get_local_offset(o[:2], rot, h, shape))
            short, longs = mh.find_shorts_longs(points)

            c = 0.0
            for s in short:
                c += als/s

            for s in longs:
                c += all/s

            h = h*c/(len(short)+len(longs))
        obj["h"] = h

        return self._get_local_offset(
            (obj["x_center"], obj["y_center"]), rot, h, shape)

    def get_closest_element(
        self,
        img: np.ndarray,
        color: str,
        shape: Optional[str]
    ) -> Optional[dict]:
        """
        Get the closest detected object of a given color and shape.

        :param img: Input image.
        :type img: np.array
        :param color: Color name.
        :type color: str
        :param shape: Shape name.
        :type shape: str
        :return: Closest object dictionary or None.
        :rtype: dict or None
        """
        computed_image: Dict[str, Any] = {"color": color}
        shape_image = self.filter_shape_color(img)
        computed_image["filtered_image"] = self.filter_color(
            img, color, shape_image)

        objects: List[dict] = []
        self.detect_obj(objects, computed_image)
        if shape is not None:
            if shape in self.shape_funcs:
                relevant_obj = self.shape_funcs["Code"](
                    objects, shape_image, shape)
            else:
                relevant_obj = self._get_correct_shape(
                    objects, shape_image, shape)
        else:
            relevant_obj = objects

        if len(relevant_obj) == 0:
            return None

        if len(relevant_obj) == 1:
            return relevant_obj[0]

        image_size = shape_image.shape[:2]

        def diag(obj: dict) -> float:
            return (obj["x_start"] - image_size[1]/2)**2 + \
                   (obj["y_start"] - image_size[1]/2)**2

        return sorted(relevant_obj, key=diag)[0]

    def _get_correct_shape(
        self,
        objects: List[dict],
        shape_image: np.ndarray,
        shape: str
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
        relevant_obj: List[dict] = []
        for obj in objects:
            if self.get_shape(obj, shape_image) == shape:
                relevant_obj.append(obj)
        return relevant_obj

    def _get_closest_code(
        self,
        objects: List[dict],
        shape_image: np.ndarray,
        shape: str
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
        relevant_obj: List[dict] = []
        for obj in objects:
            if self.find_code(obj, shape_image):
                relevant_obj.append(obj)
        return relevant_obj

    def get_filtered_objs(self) -> Dict[str, Dict[str, List[dict]]]:
        """
        Get a dictionary of all filtered objects.

        :return: Dictionary of filtered objects by color and shape.
        :rtype: dict[str, dict[str, list]]
        """
        return self._dh.get_filterd_items(self.config.get("distance_objs", 5))

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
        rot: Union[List[float], np.ndarray],
        height: float,
        imagesize: Tuple[int, int]
    ) -> np.ndarray:
        """
        Get the local offset of an object in the drone's coordinate system.

        :param obj: Object dictionary.
        :type obj: dict
        :param rot: Rotation vector.
        :type rot: list or np.array
        :param height: Height value.
        :type height: float
        :param imagesize: Image size (height, width).
        :type imagesize: tuple
        :return: Local offset [x, y, z].
        :rtype: np.array
        """
        if "contour" in obj.keys():
            return self._get_height_estimate(obj, rot, height, imagesize)
        return self._get_local_offset(
            (obj["x_center"], obj["y_center"]), rot, height, imagesize)

    def _get_local_offset(
        self,
        pixel: Tuple[int, int],
        rot: Union[List[float], np.ndarray],
        height: float,
        imagesize: Tuple[int, int]
    ) -> np.ndarray:
        """
        Internal method to compute local offset from pixel coordinates.

        :param pixel: Pixel coordinates (x, y).
        :type pixel: tuple
        :param rot: Rotation vector.
        :type rot: list or np.array
        :param height: Height value.
        :type height: float
        :param imagesize: Image size (height, width).
        :type imagesize: tuple
        :return: Local offset [x, y, z].
        :rtype: np.array
        """
        px, py = pixel
        rot_mat = mh.rotation_matrix(rot)
        rot = np.array(rot) + \
            np.array(self.config.get("rotation_offset", [0, 0, 0]))

        fov = self.config.get("fov", [66, 41])  # shape is height width
        # offset of camera position in x and y compared to drone center
        offset = np.array(self.config.get("camera_offset", [0, 0, 0]))
        local_vec = mh.compute_local(px, py, rot, imagesize, fov)

        local_vec_streched = local_vec * height / local_vec[2]
        return local_vec_streched + rot_mat @ offset

    def add_lat_lon(
        self,
        obj: dict,
        rot: Union[List[float], np.ndarray],
        height: float,
        imagesize: Tuple[int, int],
        loc_to_glo: Callable[[float, float], Any]
    ) -> None:
        """
        Add latitude and longitude to an object based on its local offset.

        :param obj: Object dictionary.
        :type obj: dict
        :param rot: Rotation vector.
        :type rot: list or np.array
        :param height: Height value.
        :type height: float
        :param imagesize: Image size (height, width).
        :type imagesize: tuple
        :param loc_to_glo: Function to convert local to global coordinates.
        :type loc_to_glo: callable
        :return: None
        """
        local_vec_streched = self.get_local_offset(obj, rot, height, imagesize)

        obj["lat_lon"] = loc_to_glo(
            local_vec_streched[0], local_vec_streched[1])
