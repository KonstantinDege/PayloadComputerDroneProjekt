class ImageAnalysis:
    def __init__(self, camera, comms):
        self._obj = []
        self._camera = camera
        self._comms = comms

    async def start_async_analysis(self, fps):
        """
        Was macht Funktion? Startet die Aufnahme der Bilder und deren Speicherung.
        Wie wird Funktion getestet? Simulation
        Wie wird Funktion funktionieren? via Pycamera2 wird Bildaufnahme mit gegebener FPS Zahl gestartet

        return
            success: bool
        """
        pass

    def get_found_obj(self):
        """
        Was macht Funktion? Gibt die gefundenen Objekte zurück.
        Wie wird Funktion getestet? unittests
        Wie wird Funktion funktionieren? Objekterkennung auf Basis von cv2
        unterfunktionen:
            def get object position: 
                Was macht Funktion? Gibt die Position des Objektes zurück.
                Wie wird Funktion getestet? unittests
                Wie wird Funktion funktionieren? Über Geometrien wird die Position des Objektes bestimmt.
                params:
                    image: Image array
                    object: Punkt in Bild
                return:
                    (x,y) position of object in coordinates
            def get color:
                Was macht Funktion? Gibt die Farbe des Objektes zurück.
                Wie wird Funktion getestet? unittests
                Wie wird Funktion funktionieren? Mittels cv2 wird die Farbe des Objektes bestimmt.
                params:
                    image: Image array
                    color: color which should be detected

                return:
                    Farbtechnisch gefiltertes Bild
        return
            obj: list of objects
            pos: list of positions
            color: list of colors
        """
        pass


    
    def stop_async_analysis(self):
        """
        Was macht Funktion? Stoppt die Aufnahme der Bilder und deren Speicherung.
        Wie wird Funktion getestet? Simulation
        Wie wird Funktion funktionieren? via Pycamera2 wird Bildaufnahme gestoppt

        return
            success: bool
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
    def quality_of_image(image):
        """
        Was macht Funktion? Überprüft die Qualität des Bildes, ob es zur Auswertung geeignet ist.
        Wie wird Funktion getestet? unittests
        Wie wird Funktion funktionieren? Es wird die Laplace-Varianz ermittelt und wenn diese unter einem bestimmten Wert ist, wird das Bild als unscharf/unbrauchbar eingestuft.

        parms:
         image: Image array

        return:
         quality: float [0,1]
        """
        pass
