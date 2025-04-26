import asyncio
import cv2
import numpy as np
from payloadcomputerdroneprojekt.camera import Camera
from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis.data_handler import DataHandler


class ImageAnalysis:
    def __init__(self, config: dict, camera: Camera, comms: Communications):
        self._obj = []
        self.config = config
        self._camera = camera
        self._comms = comms
        self._dh = DataHandler(config["path"])

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
        with self._dh as item:
            pos, rot = self._comms.get_position_latlonalt()
            item.add_position(pos, rot)
            image = self._camera.get_current_frame()
            item.add_raw_image(image)
            # TODO: Add Analysis

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

    def get_found_obj(self, image, color, position, colors_hsv):  # WIP
        """
        NOT finished
        What does the function do? Returns the detected objects.
        How is the function tested? Unit tests
        How will the function work?
            Object detection based on cv2 with prior color filtering.
        params:
            image: Image array
            color: color which should be detected []
            position: position of drone when capturing image
            colors_hsv: dict with color ranges in HSV format
        return
            obj: one list containing objects, positions and colors
        """
        image = ImageAnalysis.get_color(image, color, colors_hsv)
        for pic in image:
            if pic["color"] == "schwarz":
                image = pic["filtered image"]
                image = cv2.resize(image, (0, 0), fx=0.3, fy=0.3)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(
                contour, 0.04 * cv2.arcLength(contour, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            if len(approx) == 3:
                shape = "Dreieck"
                x_mittel = (approx[0][0][0] + approx[1]
                            [0][0] + approx[2][0][0]) // 3
                y_mittel = (approx[0][0][1] + approx[1]
                            [0][1] + approx[2][0][1]) // 3
            elif len(approx) == 4:
                shape = "Rechteck"
                x_mittel = x + (w // 2)
                y_mittel = y + (h // 2)
            elif len(approx) > 4:
                shape = "Kreis oder Ellipse"
                x_mittel = x + (w // 2)
                y_mittel = y + (h // 2)
            else:
                shape = "Unbekannt"
            cv2.circle(image, (x_mittel, y_mittel), 2, (255, 255, 255), -1)
            cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
            cv2.putText(image, shape, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    def get_color(self, image, color, colors_hsv):  # finished
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
            image: Image array
            color: color which should be detected []
            colors_hsv: dict with color ranges in HSV format

        return:
            colorfiltered images


        if image of certain color should be shown the following code can be
        used, when giving image as np.arry and hsv_farben as dict:

        farben = ["rot", "gelb", "blau", "gruen"]
        bild_gefiltert = get_color(image, farben, hsv_farben)
        desired_color = "gelb"
        for pic in bild_gefiltert:
            if pic["color"] == desired_color:
                cv2.imshow("Image", pic["filtered image"])
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """
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
                    raise KeyError(
                        f"Color '{i}' not found in the colors_hsv dictionary.")
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
            image: Image array
            obj_pos_px: point in image (pixel coordinates (only int))

        return:
            (x,y) position of object in coordinates
        """

        pass

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
    def quality_of_image(image, threshold=300):  # finished
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
         threshold: int, threshold for image quality
        return:
         quality: float [0,1]
        """

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return variance < threshold, variance
