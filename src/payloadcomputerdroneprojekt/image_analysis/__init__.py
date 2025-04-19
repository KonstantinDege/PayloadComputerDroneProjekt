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

    async def async_analysis(self, fps): # finished
        """
        finished
        What does the function do?
            Captures images and saves them at the given FPS rate.
        How is the function tested?
            Simulation
        How will the function work?
            See above.

        params:
            fps: Frames per second at which the camera should capture images; false input is handled
        """
        # test input types
        suc, fps = ImageAnalysis.test_int_type(fps)
        if not suc:
            raise ValueError("FPS must be an integer.")

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

    def start_cam(self, fps): # finished
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
            fps: Frames per second at which the camera should capture images; false input is handled
        return:
            success: bool
        """
        # test input types
        suc, fps = ImageAnalysis.test_int_type(fps)
        if not suc:
            raise ValueError("FPS must be an integer.")

        try:
            self._task = asyncio.create_task(self.async_analysis(fps))
            return True
        except Exception as e:
            print(f"Error starting the capture: {e}")
            return False

    def stop_cam(self): # finished
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
        How will the function work? Object detection based on cv2 with prior color filtering.
        params:
            image: Image array; false input is handled
            color: color which should be detected []; false input is handled
            position: position of drone when capturing image; false input is handled
        return
            obj: one list containing objects, positions and colors
        """
        # test input types
        suc, image = ImageAnalysis.test_nparray_type(image)
        if not suc:
            raise ValueError("Image must be an np array.")
        
        suc = ImageAnalysis.test_list_type(color)
        if not suc:
            raise ValueError("Color must be a list.")
        
        suc = ImageAnalysis.test_list_type(position, 6)
        if not suc:
            raise ValueError("Position must be a list with length 6.")
        
    def get_color(self, image, color, colors_hsv): # finished
        """
        finished
        capute false input
        What does the function do?
            Returns the color of the object.
        How is the function tested?
            Unit tests
        How will the function work?
            The color of the object is determined using cv2.
        params:
            image: Image array; false input is handled
            color: color which should be detected []; false input is handled
            colors_hsv: dict with color ranges in HSV format; false input is handled

        return:
            colorfiltered images


        if image of certain color should be shown the following code can be used, when giving image
        as np.arry and hsv_farben as dict:

        farben = ["rot", "gelb", "blau", "gruen"]
        bild_gefiltert = get_color(image, farben, hsv_farben)
        desired_color = "gelb"
        for pic in bild_gefiltert:
            if pic["color"] == desired_color:
                cv2.imshow("Image", pic["filtered image"])
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """
        # test input types
        suc, image = ImageAnalysis.test_nparray_type(image)
        if not suc:
            raise ValueError("Image must be an np array.")
        
        suc = ImageAnalysis.test_list_type(color)
        if not suc:
            raise ValueError("Color must be a list.")
        
        for item in colors_hsv:
            suc_list = ImageAnalysis.test_dict_type(item)
            if suc_list:
                break
        suc_dict = ImageAnalysis.test_dict_type(colors_hsv)

        if not suc_list or not suc_dict:
            raise ValueError("Colors hsv values must be provided in a dict.")

        image_show = []
        frame = image
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        for i in color:
            # red has two ranges in hsv
            if i == "rot":
                lower_red = np.array(colors_hsv["rot_1"]["lower"])
                upper_red = np.array(colors_hsv["rot_1"]["upper"])
                mask1_red = cv2.inRange(hsv, lower_red, upper_red)

                lower_red2 = np.array(colors_hsv["rot_2"]["lower"])
                upper_red2 = np.array(colors_hsv["rot_2"]["upper"])
                mask2_red = cv2.inRange(hsv, lower_red2, upper_red2)

                mask = cv2.bitwise_or(mask1_red, mask2_red)
            else:
                try:
                    lower = np.array(colors_hsv[i]["lower"])
                    upper = np.array(colors_hsv[i]["upper"])
                    mask = cv2.inRange(hsv, lower, upper)
                except KeyError:
                    raise KeyError(f"Color '{i}' not found in the colors_hsv dictionary.")
            filtered_image = cv2.bitwise_and(frame, frame, mask=mask)
            image_show.append({"color": i, "filtered image": filtered_image})

        return image_show

    def get_obj_position(self, image, obj_pos_px):
        """
        What does the function do?
            Returns the position of the object.
        How is the function tested?
            Unit tests
        How will the function work?
            The position of the object is determined using geometries.
        
        params:
            image: Image array; false input is handled
            obj_pos_px: point in image (pixel coordinates (only int)); false input is handled

        return:
            (x,y) position of object in coordinates
        """
        # test input types
        suc, image = ImageAnalysis.test_nparray_type(image)
        if not suc:
            raise ValueError("Image must be an np array.")
        
        suc = ImageAnalysis.test_tuple_only_int_type(obj_pos_px, 2)
        if not suc:
            raise ValueError("Object Position must be a tuple of length 2 with only integers.")

        pass

    def get_current_offset_closest(self, color, type_of_obj):
        """
        What does the function do?
            Returns the offset from the drone to the object.
        How is the function tested? Unit tests
        How will the function work?
            The object is detected using object detection,
            and the offset is calculated using pixels and additional geometry.

        params:
            color: color which should be detected []; false input is handled
            type_of_obj: type of object (rectangle, circle, etc.) str; false input is handled
        return
         (x,y) correct to closest
         h height estimation
        """
        # test input types
        suc = ImageAnalysis.test_list_type(color)
        if not suc:
            raise ValueError("Color must be a list.")
        
        suc, type_of_obj = ImageAnalysis.test_str_type(type_of_obj)
        if not suc:
            raise ValueError("Type of object must be a string.")
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
         image: Image array; false input is handled
         threshold: int, threshold for image quality; false input is handled
        return:
         quality: float [0,1]
        """
        suc, image = ImageAnalysis.test_nparray_type(image)
        if not suc:
            raise ValueError("Image must be an np array.")
        
        suc, threshold = ImageAnalysis.test_int_type(threshold)
        if not suc:
            raise ValueError("Threshold must be an integer.")


        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return variance < threshold, variance



    # Test input types
    @staticmethod
    def test_nparray_type(nparray): # finished
        if not isinstance(nparray, np.ndarray) or nparray.dtype != np.uint8:
            try:
                nparray = np.array(nparray, dtype=np.uint8)
                return True, nparray
            except ValueError:
                return False, None
        return True, nparray
    
    @staticmethod
    def test_int_type(input): # finished
        if not isinstance(input, int):
            try:
                input = int(float(input.replace(",", ".")))
                return True, input
            except ValueError:
                return False, None
        return True, input

    @staticmethod
    def test_list_type(input, length = 0): # finished
        if not isinstance(input, list):
            return False
        if len(input) != length and length > 0:
            return False
        return True

    @staticmethod
    def test_tuple_only_int_type(input, length = 0): # finished
        if not isinstance(input, tuple):
            return False
        if len(input) != length and length > 0:
            return False
        for item in input:
            if not isinstance(item, int):
                return False
        return True

    @staticmethod
    def test_dict_type(input): # finished
        if not isinstance(input, dict):
            return False
        return True

    @staticmethod
    def test_str_type(input): # finished
        if not isinstance(input, str):
            try:
                input = str(input)
                return True, input
            except TypeError:
                return False, None