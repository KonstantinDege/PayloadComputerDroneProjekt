import asyncio
import cv2
import numpy as np
from datetime import datetime
from payloadcomputerdroneprojekt.camera import Camera
from payloadcomputerdroneprojekt.communications import Communications


class ImageAnalysis:
    def __init__(self, camera: Camera, comms: Communications):
        self._obj = []
        self._camera = camera
        self._comms = comms

    async def async_analysis(self, fps):
        """
        finished
        What does the function do?
            Captures images and saves them at the given FPS rate.
        How is the function tested?
            Simulation
        How will the function work?
            See above.

        params:
            fps: Frames per second at which the camera should capture images (false input is handled)
        """
        # test input types
        if not ImageAnalysis.test_fps_type(fps):
            raise TypeError("FPS must be an integer.")

        interval = 1.0 / fps
        count = 0

        try:
            while True:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"image_{timestamp}.jpg"
                self._camera.capture_file(filename)
                print(f"[{count}] image saved: {filename}")
                count += 1
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            print("Capturing stopped.")

    def start_cam(self, fps):
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
            fps: Frames per second at which the camera should capture images (false input is handled)
        return:
            success: bool
        """
        # test input types
        if not ImageAnalysis.test_fps_type(fps):
            raise TypeError("FPS must be an integer.")

        try:
            self._task = asyncio.create_task(self.async_analysis(fps))
            return True
        except Exception as e:
            print(f"Error starting the capture: {e}")
            return False

    def stop_cam(self):
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
        except Exception as e:  # TODO: try finding concrete Exception Type
            print(f"Error stopping the capture: {e}")
            return False

    def get_found_obj(self, image, color, position):
        """
        What does the function do? Returns the detected objects.
        How is the function tested? Unit tests
        How will the function work? Object detection based on cv2.
        params:
            image: Image array
            color: color which should be detected []
            position: position of drone when capturing image
        return
            obj: one list containing objects, positions and colors
        """
        # test input types
        if not ImageAnalysis.test_image_type(image):
            raise TypeError("Image must be an np array.")
        if not ImageAnalysis.test_color_type(color):
            raise TypeError("color must be a list.")
        if not ImageAnalysis.test_position_type(position):
            raise TypeError("position must be a list.")

    def get_color(self, image, color, colors_hsv):
        """
        NOT finished
        capute false input
        What does the function do?
            Returns the color of the object.
        How is the function tested?
            Unit tests
        How will the function work?
            The color of the object is determined using cv2.
        params:
            image: Image array
            color: color which should be detected []
            colors_hsv: dict with color ranges in HSV format

        return:
            colorfiltered images
        """
        # test input types
        if not ImageAnalysis.test_image_type(image):
            raise TypeError("Image must be an np array.")
        if not ImageAnalysis.test_color_type(color):
            raise TypeError("color must be a list.")
        if not ImageAnalysis.test_colors_hsv_type(colors_hsv):
            raise TypeError("colors_hsv must be a dict.")

        frame = cv2.imread(image)

        height = int(frame.shape[0])
        width = int(frame.shape[1])

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        self._colors = [
            {
                "name": "rot_1",
                "lower": [0, 100, 100],
                "upper": [10, 255, 255]
            },
            {
                "name": "rot_2",
                "lower": [0, 100, 100],
                "upper": [10, 255, 255]
            }
        ]
        lower_red = np.array(colors_hsv["rot_1"]["lower"])
        upper_red = np.array(colors_hsv["rot_1"]["upper"])
        mask1_red = cv2.inRange(hsv, lower_red, upper_red)

        lower_red2 = np.array(colors_hsv["rot_2"]["lower"])
        upper_red2 = np.array(colors_hsv["rot_2"]["upper"])
        mask2_red = cv2.inRange(hsv, lower_red2, upper_red2)

        mask_red = cv2.bitwise_or(mask1_red, mask2_red)

        lower_green = np.array(colors_hsv["gruen"]["lower"])
        upper_green = np.array(colors_hsv["gruen"]["upper"])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)

        lower_blue = np.array(colors_hsv["blau"]["lower"])
        upper_blue = np.array(colors_hsv["blau"]["upper"])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        lower_yellow = np.array(colors_hsv["gelb"]["lower"])
        upper_yellow = np.array(colors_hsv["gelb"]["upper"])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

        result_red = cv2.bitwise_and(frame, frame, mask=mask_red)
        result_green = cv2.bitwise_and(frame, frame, mask=mask_green)
        result_blue = cv2.bitwise_and(frame, frame, mask=mask_blue)
        result_yellow = cv2.bitwise_and(frame, frame, mask=mask_yellow)

        # cv2.imshow("Rot", result_red)
        # cv2.imshow("Grün", result_green)
        # cv2.imshow("Blau", result_blue)
        # cv2.imshow("Gelb", result_yellow)
        # cv2.imshow("Original", frame)

        image_show = np.zeros(frame.shape, np.uint8)
        image_show[:height//2, :width //
                   2] = cv2.resize(result_red, (width//2, height//2))
        image_show[height//2:, :width //
                   2] = cv2.resize(result_green, (width//2, height//2))
        image_show[:height//2, width //
                   2:] = cv2.resize(result_blue, (width//2, height//2))
        image_show[height//2:, width //
                   2:] = cv2.resize(result_yellow, (width//2, height//2))
        # image_show = cv2.line(image_show, (width//2, 0),
        #                       (width//2, height), (255, 255, 255), 1)
        # image_show = cv2.line(image_show, (0, height//2),
        #                       (width, height//2), (255, 255, 255), 1)
        # cv2.imshow("Rot-Blau-Gruen-Gelb", image_show)

        return image_show

    def get_obj_position(self, image, object):
        """
        Was macht Funktion?
            Gibt die Position des Objektes zurück.
        Wie wird Funktion getestet?
            unittests
        Wie wird Funktion funktionieren?
            Über Geometrien wird die Position des Objektes bestimmt.
        params:
            image: Image array
            object: point in image (pixel coordinates)

        return:
            (x,y) position of object in coordinates
        """
        # test input types
        if not ImageAnalysis.test_image_type(image):
            raise TypeError("Image must be an np array.")
        if not ImageAnalysis.test_object_type(object):
            raise TypeError("object must be a tuple containing 2 integers.")

        pass

    def get_current_offset_closest(self, color, type):
        """
        What does the function do?
            Returns the offset from the drone to the object.
        How is the function tested? Unit tests
        How will the function work?
            The object is detected using object detection,
            and the offset is calculated using pixels and additional geometry.

        params:
            color: color which should be detected []
            type: type of object (rectangle, circle, etc.) str
        return
         (x,y) correct to closest
         h height estimation
        """
        # test input types
        if not ImageAnalysis.test_color_type(color):
            raise TypeError("color must be a list.")
        if not ImageAnalysis.test_object_type(type):
            raise TypeError("type must be a tuple containing 2 integers.")
        pass

    @staticmethod
    def quality_of_image(image, threshold=200):
        """
        NOT finished
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
         threshold: int, threshold for image quality
        return:
         quality: float [0,1]
        """
        # test image type




        # test threshold type




        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return variance < threshold, variance



    # Test input types
    @staticmethod
    def test_nparray_type(nparray):
        if not isinstance(nparray, np.ndarray):
            try:
                nparray = np.array(nparray, dtype=np.uint8)
                return True, nparray
            except TypeError:
                print("Input must be a uint8 np.array.")
                return False
        return True, nparray
    
    @staticmethod
    def test_int_type(int):
        if not isinstance(fps, int):
            try:
                fps = int(fps)
                return True
            except TypeError:
                print("FPS must be an integer.")
                return False

    @staticmethod
    def test_list_type(list, length):
        #list
        if not isinstance(fps, int):
            try:
                fps = int(fps)
                return True
            except TypeError:
                print("FPS must be an integer.")
                return False

    @staticmethod
    def test_tuple_type(tuple):
        # tuple with 2 int
        if not isinstance(fps, int):
            try:
                fps = int(fps)
                return True
            except TypeError:
                print("FPS must be an integer.")
                return False

    @staticmethod
    def test_dict_type(dict):
        #dict
        if not isinstance(fps, int):
            try:
                fps = int(fps)
                return True
            except TypeError:
                print("FPS must be an integer.")
                return False
