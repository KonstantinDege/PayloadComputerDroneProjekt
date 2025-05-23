import asyncio
import cv2
import numpy as np
from payloadcomputerdroneprojekt.camera.abstract_class import AbstractCamera
from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis.data_handler import DataHandler
import payloadcomputerdroneprojekt.image_analysis.math_helper as mh
import tempfile
from payloadcomputerdroneprojekt.helper import smart_print as sp
import time


class ImageAnalysis:
    def __init__(self, config: dict,
                 camera: AbstractCamera, comms: Communications):
        self._obj = []
        self.config = config
        self._camera = camera
        self._comms = comms
        self._task = None
        self._dh = DataHandler(config.setdefault(
            "path", tempfile.mkdtemp(prefix="image_analysis")))

        def conhsv(val):
            return np.array([val[0] * 2.55, val[1] + 128, val[2] + 128])
        self.colors: dict = {}
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

        self.shape_color = {
            "lower": conhsv(config["shape_color"]["lower"]),
            "upper": conhsv(config["shape_color"]["upper"])
        }

        self.shape_funcs = {
            "Code": self._get_closest_code
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
            sp(f"starting camera with {ips}")
            self._task = asyncio.create_task(self._async_analysis(ips))
            return True
        except Exception as e:
            sp(f"Error starting the capture: {e}")
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
        except Exception as e:
            sp(f"Error stopping the capture: {e}")
            return False

    async def take_image(self):
        try:
            await self._take_image()
        except Exception as e:
            sp(f"Take image failed {e}")
            return False
        return True

    async def _take_image(self):
        if not self._camera.is_active:
            self._camera.start_camera()
            await asyncio.sleep(2)
        await self.image_loop()

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
            sp(f"Could not convert ips to float, using Standard ips=1; {e}")
            ips = 1.0
        interval = 1.0 / ips
        count = 0

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
        Wraps the logik that runs the analysis each frame.
        """
        st = time.time()
        image = self._camera.get_current_frame()
        pos_com = await self._comms.get_position_lat_lon_alt()
        if st - time.time() < 0.25:
            self._image_sub_routine(image, pos_com, pos_com[2])
        else:
            sp("skipped image")

    def _image_sub_routine(self, image, pos_com, height):
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

            loc_to_glo = mh.local_to_global(pos_com[0], pos_com[1])

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
        gray = filtered_image["filtered_image"]
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
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

    def get_shape(self, obj: dict, shape_image: np.array, save_contour=False):
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

    def find_code(self, obj: dict, shape_image: np.array):
        bound_box = obj["bound_box"]

        subframe = shape_image[bound_box["y_start"]:bound_box["y_stop"],
                               bound_box["x_start"]:bound_box["x_stop"]]

        gray = subframe
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        code_elements = []
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
                code_elements, lambda x: x["d"], reverse=True)[:3]
        return True

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
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        shape_mask = self._filter_color(
            hsv, self.shape_color)
        for name, elements in self.colors.items():
            image_show.append(
                {"color": name,
                 "filtered_image": self._filter_color(
                     hsv, elements, shape_mask=shape_mask)})

        return image_show, shape_mask

    def filter_shape_color(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        return self._filter_color(
            hsv, self.shape_color)

    def filter_color(self, image: np.array,
                     color: str, shape_mask=None) -> np.array:
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
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        if shape_mask is not None:
            shape_mask = self._filter_color(
                hsv, self.shape_color)
        return self._filter_color(hsv, self.colors[color],
                                  shape_mask=shape_mask)

    def _filter_color(self, lab, elements: dict, shape_mask=None):
        if isinstance(elements, list):
            masks = []
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

    async def get_current_offset_closest(self, color: str,
                                         shape: str, yaw_0: bool = True):
        """
        What does the function do?
            Returns the offset from the drone to the object.
        How is the function tested? simulation / unit tests
        How will the function work?
            The object is detected using object detection,
            and the offset is calculated using pixels and additional geometry.

        params:
            color: color which should be detected []
            shape: pixel coordinates of object tuple (x,y)
        return
         (x,y) correct to closest
         h height estimation
         yaw offset
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
            self, pos: list[float], dh: float, img: np.array, color: str,
            shape: str, yaw_0: bool = True):

        closest_obj = self.get_closest_element(img, color, shape)
        if closest_obj is None:
            return None, None, None

        if yaw_0:
            pos[5] = 0

        if "code" in closest_obj.keys():
            return self._get_height_estimate_yaw(
                closest_obj, pos[3:6], dh, img.shape[:2])
        pos = self._get_height_estimate(
            closest_obj, pos[3:6], dh, img.shape[:2])
        return [float(pos[0]), float(pos[1])], float(pos[2]), 0

    def _get_height_estimate_yaw(self, obj, rot, h_start, shape):
        al = self.config.get("length_code_side", 0.5)
        h = h_start
        t_l, b_l, t_r = mh.find_rel_position(
            [(c["x"]+c["w"]/2, c["y"]+c["h"]/2, 0) for c in obj["code"]])
        for i in range(5):
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

    def _get_height_estimate(self, obj, rot, h_start, shape):
        als = self.config.get("length_box_short_side", 0.4)
        all = self.config.get("length_box_long_side", 0.6)
        h = h_start

        for i in range(3):
            points = []
            for o in obj["contour"]:
                points.append(self._get_local_offset(o[:2], rot, h, shape))
            short, longs = mh.find_shorts_longs(points)

            c = 0
            for s in short:
                c += als/s

            for s in longs:
                c += all/s

            h = h*c/(len(short)+len(longs))
        obj["h"] = h

        return self._get_local_offset(
            (obj["x_center"], obj["y_center"]), rot, h, shape)

    def get_closest_element(self, img, color, shape) -> dict:
        computed_image = {"color": color}
        shape_image = self.filter_shape_color(img)
        computed_image["filtered_image"] = self.filter_color(
            img, color, shape_image)

        objects: list[dict] = []
        self.detect_obj(objects, computed_image)

        if shape in self.shape_funcs:
            relevant_obj = self.shape_funcs["Code"](
                objects, shape_image, shape)
        else:
            relevant_obj = self._get_correct_shape(
                objects, shape_image, shape)

        if len(relevant_obj) == 0:
            return None

        if len(relevant_obj) == 1:
            return relevant_obj[0]

        image_size = shape_image.shape[:2]

        def diag(obj):
            return (obj["x_start"] - image_size[1]/2)**2 + \
                   (obj["y_start"] - image_size[1]/2)**2

        return sorted(relevant_obj, diag)[0]

    def _get_correct_shape(self, objects, shape_image, shape):
        relevant_obj = []
        for obj in objects:
            if self.get_shape(obj, shape_image, True) == shape:
                relevant_obj.append(obj)
        return relevant_obj

    def _get_closest_code(self, objects, shape_image, shape):
        relevant_obj = []
        for obj in objects:
            if self.find_code(obj, shape_image):
                relevant_obj.append(obj)
        return relevant_obj

    def get_filtered_objs(self):
        """
        Returns a list of all filtered obj

        Returns:
            dict[str, dict[str, list]]: _description_
        """
        return self._dh.get_filterd_items(self.config.get("distance_objs", 5))

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

        return self.get_filtered_objs().get(color, {}).get(shape, [])

    def get_color_obj_list(self, color: str) -> list[dict]:
        out = []
        for shape, obj in self.get_filtered_objs().get(color, {}).items():
            obj["shape"] = shape
            out.append(obj)
        return out

    def get_all_obj_list(self) -> list[dict]:
        out = []
        for color, objs in self.get_filtered_objs().items():
            for shape, obj in objs.items():
                obj["color"] = color
                obj["shape"] = shape
                out.append(obj)
        return out

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

        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        return laplacian.var()

    def get_local_offset(self, obj, rot, height, imagesize):
        if "contour" in obj.keys():
            return self._get_height_estimate(obj, rot, height, imagesize)
        return self._get_local_offset(
            (obj["x_center"], obj["y_center"]), rot, height, imagesize)

    def _get_local_offset(self, pixel, rot, height, imagesize):
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

    def add_lat_lon(self, obj, rot, height, imagesize, loc_to_glo):
        local_vec_streched = self.get_local_offset(obj, rot, height, imagesize)

        obj["lat_lon"] = loc_to_glo(
            local_vec_streched[0], local_vec_streched[1])
