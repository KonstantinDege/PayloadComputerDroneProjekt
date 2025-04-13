import asyncio
import cv2
import numpy as np
from datetime import datetime

class ImageAnalysis:
    def __init__(self, camera, comms):
        self._obj = []
        self._camera = camera
        self._comms = comms

    async def async_analysis(self, fps):
        """
        Fertig
        Was macht Funktion? Nimmt Bilder auf und speichert sie mit gegebener FPS Zahl.
        Wie wird Funktion getestet? Simulation
        Wie wird Funktion funktionieren? s.o.

        params:
            fps: Frames per second, mit der die Kamera aufnehmen soll
        """
        interval = 1.0 / fps
        count = 0

        try:
            while True:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"image_{timestamp}.jpg"
                self._camera.capture_file(filename)
                print(f"[{count}] Bild gespeichert: {filename}")
                count += 1
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            print("Aufnahme gestoppt.")        


    def start_cam(self, fps):
        """
        fertig
        Was macht Funktion? Startet die Aufnahme der Bilder und deren Speicherung.
        Wie wird Funktion getestet? Simulation
        Wie wird Funktion funktionieren? es wird ein asynchroner Task gestart, der die Bilder aufnimmt und speichert, sodass der weitere 
                                        Programmablauf nicht gestört wird.

        params:
            fps: Frames per second, mit der die Kamera aufnehmen soll
        return:
            success: bool
        """
        try:
            self._task = asyncio.create_task(self.async_analysis(fps))
            return True
        except Exception as e:
            print(f"Fehler beim Starten der Aufnahme: {e}")
            return False
        


    def stop_cam(self):
        """
        fertig
        Was macht Funktion? Stoppt die Aufnahme der Bilder und deren Speicherung.
        Wie wird Funktion getestet? Simulation
        Wie wird Funktion funktionieren? es wird ein asynchroner Task gestoppt

        return:
            success: bool
        """
        try:
            self._task.cancel()
            return True
        except:
            print("Aufnahme bereits gestoppt.")
            return False


    def get_found_obj(self, image, color, position):
        """
        Was macht Funktion? Gibt die gefundenen Objekte zurück.
        Wie wird Funktion getestet? unittests
        Wie wird Funktion funktionieren? Objekterkennung auf Basis von cv2
        params:
            image: Image array
            color: color which should be detected []
            position: position of object
        return
            obj: list of objects
            pos: list of positions
            color: list of colors
        """
        pass

    def get_color(self, image, color, colors_hsv):
        """
        auf variable Anzahl an Farben anpassen
        Was macht Funktion? Gibt die Farbe des Objektes zurück.
        Wie wird Funktion getestet? unittests
        Wie wird Funktion funktionieren? Mittels cv2 wird die Farbe des Objektes bestimmt.
        params:
            image: Image array
            color: color which should be detected []

        return:
            Farbtechnisch gefilterte Bilder nach Farben
        """
        frame = cv2.imread(image)

        height = int(frame.shape[0])
        width = int(frame.shape[1])

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

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

        #cv2.imshow("Rot", result_red)
        #cv2.imshow("Grün", result_green)
        #cv2.imshow("Blau", result_blue)
        #cv2.imshow("Gelb", result_yellow)
        #cv2.imshow("Original", frame)

        image_show = np.zeros(frame.shape, np.uint8)
        image_show[:height//2, :width//2] = cv2.resize(result_red, (width//2, height//2))
        image_show[height//2:, :width//2] = cv2.resize(result_green, (width//2, height//2))
        image_show[:height//2, width//2:] = cv2.resize(result_blue, (width//2, height//2))
        image_show[height//2:, width//2:] = cv2.resize(result_yellow, (width//2, height//2))
        #image_show = cv2.line(image_show, (width//2, 0), (width//2, height), (255, 255, 255), 1)
        #image_show = cv2.line(image_show, (0, height//2), (width, height//2), (255, 255, 255), 1)
        #cv2.imshow("Rot-Blau-Gruen-Gelb", image_show)

        return image_show
    

    def get_obj_position(self, image, object):
        """
        Was macht Funktion? Gibt die Position des Objektes zurück.
        Wie wird Funktion getestet? unittests
        Wie wird Funktion funktionieren? Über Geometrien wird die Position des Objektes bestimmt.
        params:
            image: Image array
            object: Punkt in Bild

        return:
            (x,y) position of object in coordinates
        """
        pass

    def get_current_offset_closest(self, color, type):
        """
        Was macht Funktion? Gibt Offset von Drohne zu Objekt zurück.
        Wie wird Funktion getestet? unittests
        Wie wird Funktion funktionieren? Mittels Objekterkennung wird Objekt erkannt und dann über Pixel und weiterer Geometrie der Offset berechnet.

        return
         (x,y) correct to closest
         h height estimation
        """
        pass

    @staticmethod 
    def quality_of_image(image, threshold=200):
        """
        NICHT fertig
        Was macht Funktion? Überprüft die Qualität des Bildes, ob es zur Auswertung geeignet ist.
        Wie wird Funktion getestet? unittests
        Wie wird Funktion funktionieren? Es wird die Laplace-Varianz ermittelt und wenn diese unter einem bestimmten Wert ist, wird das Bild als unscharf/unbrauchbar eingestuft.

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
        

