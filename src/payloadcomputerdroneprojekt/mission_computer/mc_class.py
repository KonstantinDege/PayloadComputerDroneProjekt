from payloadcomputerdroneprojekt.communications \
    import Communications  # importiert die Klasse Communications
from payloadcomputerdroneprojekt.image_analysis \
    import ImageAnalysis  # importiert die Klasse ImageAnalysis
from payloadcomputerdroneprojekt.camera \
    import AbstractCamera  # importiert die abstrakte Kamera-Klasse
from payloadcomputerdroneprojekt.mission_computer.helper \
    import rec_serialize, count_actions, action_with_count, diag, \
    find_shortest_path  # importiert Hilfsfunktionen für die Missionsplanung
import os  \
    # Zugriff auf Betriebssystemfunktionen (Dateipfade, Umgebungsvariablen etc)
import logging  \
    # Ermöglicht Logging von Status- oder Fehlermeldungen – wichtig für Nachvollziehbarkeit und Debugging
import time  # Zugriff auf Zeitfunktionen, z. B. time.sleep() oder Zeitstempel
import json  # JSON-Verarbeitung für Missionsdateien und Fortschrittsdateien
import shutil  # Ermöglicht das Kopieren und Löschen von Dateien
from payloadcomputerdroneprojekt.helper \
    import smart_print as sp  # Importiert eine benutzerdefinierte Funktion zum Drucken von Nachrichten
import asyncio  # Ermöglicht die Nutzung von asynchronem Code (z. B. async def, await), was wichtig ist, wenn viele Operationen gleichzeitig ablaufen (z. B. Kamera läuft, Kommunikation wird verarbeitet etc.)
from typing \
    import Any, Callable, Dict, List, Optional  # Diese Typen werden für statische Typüberprüfungen und bessere Lesbarkeit genutzt

MISSION_PATH = "mission_file.json"  # Pfad zur Missionsdatei, die die Missionsplanung enthält
MISSION_PROGRESS = "__mission__.json"  # Pfad zur Fortschrittsdatei, die den aktuellen Fortschritt der Mission speichert


# ↓↓↓↓↓↓↓↓↓↓
# Diese Funktion prüft, ob eine Datei unter dem angegebenen Pfad existiert,
# und löscht sie, falls ja. Sie dient dazu, alte oder unnötige Dateien
# (z. B. Missionsdaten) vor dem Start einer neuen Mission zu entfernen

def test_rem(path: str) -> None:  # Dies ist die Funktionsdefinition. # path: str bedeutet: Die Funktion erwartet einen String, der einen Dateipfad repräsentiert. # -> None sagt: Die Funktion gibt keinen Rückgabewert zurück – sie führt nur eine Aktion aus.
    if os.path.exists(path):  # Überprüft, ob die Datei unter dem angegebenen Pfad existiert
        os.remove(path)  # Wenn die Datei existiert, wird sie gelöscht

# ↓↓↓↓↓↓↓↓↓↓
# Die Klasse MissionComputer ist das zentrale Steuerungselement der Drohne. Sie verwaltet:
# den Missionsablauf,
# die Kommunikation mit Pixhawk, Raspberry Pi und Groundstation,
# die Bildanalyse mit einer Kamera,
# und die Fortschrittsverfolgung.


class MissionComputer:  # Definition der Klasse MissionComputer
    """
    MissionComputer class for managing drone missions, communication, and image
    analysis.

    This class handles mission initialization, execution, progress tracking,
    and communication with the drone and its subsystems.

    :param config: Configuration dictionary for the mission computer and
        subsystems.
    :type config: dict
    :param port: Communication port for the drone.
    :type port: str
    :param camera: Camera class to be used for image analysis.
    :type camera: type[AbstractCamera]
    :param communications: Communications class for drone communication.
    :type communications: type[Communications], optional
    :param image_analysis: ImageAnalysis class for image processing.
    :type image_analysis: type[ImageAnalysis], optional
    """
    # ↓↓↓↓↓↓↓↓↓↓
    # Die Methode __init__ richtet alle Komponenten des Missionscomputers ein:
    # sie legt das Arbeitsverzeichnis fest,
    # startet das Logging,
    # initialisiert Kommunikation und Bildverarbeitung,
    # startet die Kamera,
    # lädt die spezifischen Einstellungen für den Missionscomputer
    # und führt abschließend die interne Setup-Funktion _setup() aus.

    def __init__(  # Konstruktor der Klasse MissionComputer
        self,  # self ist eine Referenz auf die Instanz der Klasse, die erstellt wird
        config: dict,  # Konfigurationsdaten für den Missionscomputer, die Kamera und andere Komponenten
        port: str,  # Kommunikationsport für die Drohne (z. B. /dev/ttyUSB0)
        camera: type[AbstractCamera],  # Kameraklasse, die für die Bildanalyse verwendet wird (z. B. PiCamera)
        communications: type[Communications] = Communications,  # Kommunikationsklasse, die für die Kommunikation mit der Drohne verwendet wird (standardmäßig Communications)
        image_analysis: type[ImageAnalysis] = ImageAnalysis  # Bildanalyseklasse, die für die Bildverarbeitung verwendet wird (standardmäßig ImageAnalysis)
    ) -> None:  # -> None gibt an, dass diese Methode keinen Rückgabewert hat

        """
        Initialize the MissionComputer instance.

        Sets up communication, image analysis, logging, and working directory.

        :param config: Configuration dictionary.
        :type config: dict
        :param port: Communication port.
        :type port: str
        :param camera: Camera class.
        :type camera: type[AbstractCamera]
        :param communications: Communications class.
        :type communications: type[Communications], optional
        :param image_analysis: ImageAnalysis class.
        :type image_analysis: type[ImageAnalysis], optional
        """
        self.set_work_dir(config)  # Setzt das Arbeitsverzeichnis basierend auf der Konfiguration
        logging.basicConfig(filename="flight.log",  # Konfiguriert das Logging
                            format='%(asctime)s %(message)s',  # legt das Format der Log-Nachrichten fest
                            level=logging.INFO)  # legt das Log-Level fest (INFO, DEBUG, etc.)

        self._comms: Communications = communications(  # Erstellt ein Objekt der Kommunikationsklasse (Communications) und speichert es in self._comms.
            port, config.get("communications", {}))  # Initialisiert die Kommunikation mit dem angegebenen Port und Konfiguration

        self._image: ImageAnalysis = image_analysis(  #  Initialisiert die Bildanalyse (ImageAnalysis):
            config=config.get("image", {}), camera=camera(  # Erstellt ein Objekt der Kameraklasse (z. B. PiCamera) mit den Konfigurationen aus config["image"]
                config.get("camera", None)), comms=self._comms)  # Übergibt die Kommunikationsinstanz an die Bildanalyse

        self._image._camera.start_camera()  # Startet die Kamera, um Bilder zu erfassen
        self.config: dict = config.get("mission_computer", {})  # Speichert die Konfiguration für den Missionscomputer

        self._setup()  # Führt die interne Setup-Funktion aus, um den Missionsplan, Fortschritt und verfügbare Aktionen zu initialisieren
    
    # ↓↓↓↓↓↓↓↓↓↓
    # Die Funktion legt das Arbeitsverzeichnis fest,
    # in dem z. B. Missionsdateien gespeichert werden.
    # Falls der Pfad nicht existiert oder nicht erstellt werden kann,
    # wird automatisch auf ein Standardverzeichnis ("mission_storage")
    # gewechselt. Fehler werden im Log dokumentiert.

    def set_work_dir(self, config: dict) -> None:  # Methode zum Setzen des Arbeitsverzeichnisses
        error: Optional[Exception] = None  # Initialisiert eine Variable für Fehler, die später geloggt werden können
        try:  # Versucht, das Arbeitsverzeichnis basierend auf der Konfiguration zu setzen
            path: str = config.get("mission_storage", "mission_storage")  # Versucht, den Pfad aus der Konfiguration zu laden, sonst Standardverzeichnis "mission_storage"
            print(path)  # Gibt den Pfad aus, um zu sehen, wo die Missionsdateien gespeichert werden
            os.makedirs(path, exist_ok=True)  # Erstellt das Verzeichnis, falls es nicht existiert (exist_ok=True verhindert Fehler, wenn das Verzeichnis bereits existiert)
        except Exception as e:  # Wenn ein Fehler auftritt (z. B. Berechtigungsprobleme oder ungültiger Pfad)
            error = e  # Speichert den Fehler in der Variable error
            print(
                "Working directory not accesable, "
                "switching to 'mission_storage'")  # Gibt eine Fehlermeldung aus, dass das Arbeitsverzeichnis nicht zugänglich ist und auf "mission_storage" gewechselt wird
            path = "mission_storage"  # Setzt den Pfad auf das Standardverzeichnis "mission_storage"
            os.makedirs(path, exist_ok=True)  # Erstellt das Standardverzeichnis, falls es nicht existiert
        os.chdir(path)  # Wechselt in das Arbeitsverzeichnis, damit alle Dateipfade relativ zu diesem Verzeichnis sind
        if error:  # Wenn ein Fehler aufgetreten ist
            logging.info(str(error))  # Loggt den Fehler, um ihn später zu überprüfen

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode initialisiert den Zustand des Missionscomputers:
    # Sie legt fest, was gerade läuft (Tasks),
    # bereitet den Missionsplan und Fortschrittszähler vor,
    # definiert alle verfügbaren Missionsaktionen als aufrufbare Methoden,
    # markiert bestimmte Aufgaben als "nicht zählbar" für Fortschrittsanzeigen,
    # und listet Tasks auf, die beim Abbruch einer Mission gestoppt werden sollen.

    def _setup(self) -> None:  # Interne Setup-Methode, die den Missionsplan, Fortschritt und verfügbare Aktionen initialisiert
        """
        Internal setup for mission plan, progress, and available actions.
        """
        self.task = None  # Aktuelle Aufgabe, die ausgeführt wird (wird später gesetzt)
        self._old_task = None  # Vorherige Aufgabe, die ausgeführt wurde (wird später gesetzt)
        self.current_mission_plan: dict = {}  # Aktueller Missionsplan, der die Aktionen und Parameter enthält
        self.current_mission_plan.setdefault("parameter", {})  # Stellt sicher, dass der Missionsplan immer ein "parameter"-Feld hat, auch wenn es leer ist
        self.progress: int = 0  # Aktueller Fortschritt der Mission, initialisiert auf 0
        self.max_progress: int = -1  # Maximale Anzahl an Aktionen im Missionsplan, initialisiert auf -1 (unbekannt)
        self.running: bool = False  # Flag, das angibt, ob eine Mission gerade läuft (initialisiert auf False)
        self.main_programm: Optional[asyncio.Task] = None  # Hauptprogramm-Task, der die Mission ausführt (initialisiert auf None)
        self.actions: Dict[str, Callable] = {  # Dictionary, das die verfügbaren Aktionen und ihre zugehörigen Methoden enthält
            "start_camera": self.start_camera,  # Startet die Kamera
            "stop_camera": self.stop_camera,  # Stoppt die Kamera und verarbeitet gefilterte Objekte
            "takeoff": self.takeoff,  # Startet die Drohne und hebt sie auf eine bestimmte Höhe
            "land_at": self.land,  # Lässt die Drohne an einem bestimmten Ort landen
            "delay": self.delay,  # Verzögert die Ausführung für eine bestimmte Zeit
            "list": self.execute_list,  # Führt eine Liste von Aktionen aus
            "mov_multiple": self.mov_multiple,  # Bewegt die Drohne zu mehreren Positionen
            "forever": self.forever,  # Führt eine Endlosschleife aus (z. B. für Tests)
            "mov": self.mov,  # Bewegt die Drohne zu einer bestimmten Position (Latitude, Longitude, Höhe)
            "mov_to_objects_cap_pic": self.mov_to_objects_cap_pic,  # Bewegt die Drohne zu erkannten Objekten und macht Bilder
        }
        self.none_counting_tasks: List[str] = [  # Liste von Aktionen, die nicht zum Fortschritt zählen
            "list", "mov_multiple"  # Aktionen, die nicht zum Fortschritt zählen
        ]
        self.cancel_list: List[Callable] = [  # Liste von Tasks, die beim Abbruch einer Mission gestoppt werden sollen
            self._image.stop_cam  # Stoppt die Kamera
        ]
        # TODO: add on off state filter camera is
        # not being reactivated on restart

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode lädt eine Missionsdatei (z. B. aus einer .json) und stellt
    # entweder den gespeicherten Fortschritt wieder her oder startet
    # die Mission von vorn.
    # Sie prüft:
    # ob ein Missionsfortschritt gespeichert ist,
    # ob dieser noch gültig ist (Zeitfenster),
    # ob eine Missionsdatei vorhanden ist,
    # und setzt self.current_mission_plan, self.progress und self.max_progress.

    def initiate(self, missionfile: str = "") -> None:  # Methode zum Starten oder Zurücksetzen des Missionsplans
        """
        Initialize or reset the mission plan from a file.

        :param missionfile: Path to the mission file.
        :type missionfile: str, optional
        """
        if os.path.exists(MISSION_PROGRESS):  # Überprüft, ob eine Fortschrittsdatei existiert
            try:  # Versucht, den Fortschritt aus der Datei zu lesen
                with open(MISSION_PROGRESS, "r") as f:  # Öffnet die Fortschrittsdatei im Lesemodus
                    progress = json.load(f)  # Lädt den Fortschritt als JSON-Objekt
            # Check if the mission can be recovered based on time
                if abs(progress["time"] - time.time()
                       ) > self.config.get("recouver_time", 10):  # Überprüft, ob der Fortschritt innerhalb des zulässigen Zeitfensters liegt
                    test_rem(MISSION_PROGRESS)  # Wenn der Fortschritt zu alt ist, wird die Fortschrittsdatei gelöscht
                    test_rem(MISSION_PATH)  # und die Missionsdatei entfernt
            except Exception:  # Wenn ein Fehler beim Lesen der Fortschrittsdatei auftritt
                sp("Error reading progress file, resetting progress")  # Gibt eine Fehlermeldung aus
                test_rem(MISSION_PROGRESS)  # Löscht die Fortschrittsdatei
                test_rem(MISSION_PATH)  # und entfernt die Missionsdatei
                return  # Beendet die Methode, da kein gültiger Fortschritt vorhanden ist

        mission: Optional[dict] = None  # Initialisiert die Variable mission, die später den Missionsplan enthalten wird
        if os.path.exists(missionfile):  # Überprüft, ob eine Missionsdatei existiert
            shutil.copyfile(missionfile, MISSION_PATH)  # Kopiert die Missionsdatei an den Standardpfad MISSION_PATH
            test_rem(MISSION_PROGRESS)  # Löscht die Fortschrittsdatei, da eine neue Mission gestartet wird

        if os.path.exists(MISSION_PATH):  # Überprüft, ob die Missionsdatei existiert
            with open(MISSION_PATH, "r") as f:  # Öffnet die Missionsdatei im Lesemodus
                mission = json.load(f)  # Lädt den Missionsplan als JSON-Objekt
                rec_serialize(mission)  # Rekursive Serialisierung des Missionsplans, um sicherzustellen, dass alle Aktionen korrekt geladen werden
                self.current_mission_plan = mission  # Setzt den aktuellen Missionsplan auf den geladenen Plan
                self.current_mission_plan.setdefault("parameter", {})  # Stellt sicher, dass der Missionsplan immer ein "parameter"-Feld hat, auch wenn es leer ist

        if mission is None:  # Wenn kein Missionsplan geladen werden konnte
            self.progress = 0  # Setzt den Fortschritt auf 0
            self.max_progress = -1  # Setzt die maximale Anzahl an Aktionen auf -1 (unbekannt)
            test_rem(MISSION_PROGRESS)  # Löscht die Fortschrittsdatei, da keine Mission gestartet werden kann
            return  # Beendet die Methode, da kein gültiger Missionsplan vorhanden ist
        try:  # Versucht, den Fortschritt aus der Fortschrittsdatei zu laden
            if os.path.exists(MISSION_PROGRESS):  # Überprüft, ob eine Fortschrittsdatei existiert
                with open(MISSION_PROGRESS, "r") as f:  # Öffnet die Fortschrittsdatei im Lesemodus
                    progress = json.load(f)  # Lädt den Fortschritt als JSON-Objekt
                if count_actions(mission) == progress["max_progress"]:  # Überprüft, ob die maximale Anzahl an Aktionen im Missionsplan mit dem gespeicherten Fortschritt übereinstimmt
                    self.progress = progress["progress"]  # Setzt den aktuellen Fortschritt auf den gespeicherten Wert
                    self.max_progress = progress["max_progress"]  # Setzt die maximale Anzahl an Aktionen auf den gespeicherten Wert
                    return  # Beendet die Methode, da der Fortschritt erfolgreich geladen wurde
        except Exception:  # Wenn ein Fehler beim Lesen der Fortschrittsdatei auftritt
            sp("Error reading progress file, resetting progress")  # Gibt eine Fehlermeldung aus
            test_rem(MISSION_PROGRESS)  # Löscht die Fortschrittsdatei
            self.progress = 0  # Setzt den Fortschritt auf 0
            self.max_progress = -1  # Setzt die maximale Anzahl an Aktionen auf -1 (unbekannt)
            return  # Beendet die Methode, da kein gültiger Fortschritt geladen werden konnte

        self.progress = mission.get("progress", 0)  # Setzt den aktuellen Fortschritt auf den gespeicherten Wert oder 0, wenn nicht vorhanden
        self.max_progress = count_actions(mission)  # Berechnet die maximale Anzahl an Aktionen im Missionsplan

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode läuft dauerhaft im Hintergrund und speichert alle 100 ms
    # den aktuellen Fortschritt in eine Datei (__mission__.json).
    # Sie nutzt asyncio, um nicht blockierend zu arbeiten und parallel
    # zur Mission weiterzulaufen.

    async def save_progress(self) -> None:  # Methode zum periodischen Speichern des Fortschritts
        """
        Periodically save the current mission progress to a file.
        """
        while True:  # Endlosschleife, die alle 100 ms den Fortschritt speichert
            self._save_progress()  # Ruft die interne Methode zum Speichern des Fortschritts auf
            await asyncio.sleep(0.1)  # Wartet 100 ms, bevor der Fortschritt erneut gespeichert wird

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Funktion speichert den aktuellen Fortschrittsstand
    # (progress, max_progress) und den aktuellen Zeitstempel in
    # die Datei __mission__.json, aber nur, wenn gerade eine
    # Mission läuft (self.running == True).

    def _save_progress(self) -> None:  # Interne Methode zum Speichern des Fortschritts
        """
        Save the current progress to the progress file if the mission is
        running.
        """
        if self.running:  # Überprüft, ob eine Mission gerade läuft
            obj = {
                "progress": self.progress,
                "max_progress": self.max_progress,
                "time": time.time()
            }  # Erstellt ein Dictionary mit dem aktuellen Fortschritt, der maximalen Anzahl an Aktionen und dem aktuellen Zeitstempel
            with open(MISSION_PROGRESS, "w") as f:  # Öffnet die Fortschrittsdatei im Schreibmodus
                json.dump(obj, f)  # Speichert das Dictionary als JSON-Objekt in der Datei

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode führt eine Aktion aus dem Missionsplan aus:
    # Sie prüft, ob die Aktion bekannt ist,
    # ruft die passende Methode aus dem self.actions-Dictionary auf,
    # zählt den Fortschritt mit (außer bei speziellen Aktionen),
    # speichert den neuen Status,
    # und beendet ggf. die Mission, wenn alle Schritte erledigt sind.

    async def execute(self, action: dict) -> None:  # Methode zum Ausführen einer einzelnen Aktion aus dem Missionsplan
        """
        Execute a single mission action.

        :param action: Action dictionary containing the action type and
            commands.
        :type action: dict
        """
        self.running = True  # Setzt das Flag running auf True, um anzuzeigen, dass eine Mission läuft
        a: str = action["action"]  # Extrahiert den Aktionstyp aus dem Aktions-Dictionary

        if a not in self.actions.keys():  # Überprüft, ob die Aktion im Dictionary der verfügbaren Aktionen vorhanden ist
            sp(f"Action not found {a} at exectuion"
               f" {self.progress} / {self.max_progress}")  # Gibt eine Fehlermeldung aus, wenn die Aktion nicht gefunden wurde
            return  # Beendet die Methode, da die Aktion nicht ausgeführt werden kann
        try:  # Versucht, die Aktion auszuführen
            await self.actions[a](action.get("commands", {}))  # Ruft die passende Methode aus dem self.actions-Dictionary auf und übergibt die Befehle der Aktion
        except Exception as e:  # Wenn ein Fehler bei der Ausführung der Aktion auftritt
            sp(f"Error in {a} ({self.progress} / {self.max_progress}): {e}")  # Gibt eine Fehlermeldung aus, die den Fehler beschreibt
        if a not in self.none_counting_tasks:  # Überprüft, ob die Aktion nicht in der Liste der nicht zählenden Aktionen enthalten ist
            self.progress += 1  # Erhöht den Fortschritt um 1, wenn die Aktion zum Fortschritt zählt

        self._save_progress()  # Speichert den aktuellen Fortschritt in der Fortschrittsdatei
        self.running = False  # Setzt das Flag running auf False, um anzuzeigen, dass die Mission abgeschlossen ist
        if self.progress >= self.max_progress:  # Überprüft, ob der Fortschritt die maximale Anzahl an Aktionen erreicht hat
            await self.status("Mission Completed")  # Gibt eine Statusmeldung aus, dass die Mission abgeschlossen ist
            self.running = False  # Setzt das Flag running auf False, um anzuzeigen, dass die Mission abgeschlossen ist
            if os.path.exists(MISSION_PROGRESS):  # Überprüft, ob die Fortschrittsdatei existiert
                os.remove(MISSION_PROGRESS)  # Löscht die Fortschrittsdatei, da die Mission abgeschlossen ist
            if os.path.exists(MISSION_PATH):  # Überprüft, ob die Missionsdatei existiert
                os.remove(MISSION_PATH)  # Löscht die Missionsdatei, da die Mission abgeschlossen ist

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode startet die Haupt-Eventschleife des Missionscomputers.
    # Sie speichert den Task-Eintrag (self.task = self._start)
    # und ruft dann die Methode self._task() innerhalb der
    # asyncio-Laufzeitumgebung auf – das ist der zentrale Ablauf der Mission.
 
    def start(self) -> None:  # Methode zum Starten der Haupt-Eventschleife des Missionscomputers
        """
        Start the mission computer's main event loop.
        """
        self.task = self._start  # Setzt die aktuelle Aufgabe auf die Methode _start, die die Haupt-Eventschleife startet
        asyncio.run(self._task())  # Startet die asynchrone Task-Eventschleife, die die Mission ausführt

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode läuft dauerhaft in einer Schleife und überprüft
    # regelmäßig, ob eine neue Aufgabe (self.task) ausgeführt werden soll.
    # Wenn ja, wird eine eventuell noch laufende alte Aufgabe (self._old_task)
    # abgebrochen und durch eine neue asyncio-Task ersetzt.

    async def _task(self) -> None:  # Interne Methode, die die Haupt-Eventschleife des Missionscomputers ausführt
        while True:  # Endlosschleife, die ständig nach neuen Aufgaben sucht
            if self.task is not None:  # Überprüft, ob eine neue Aufgabe vorhanden ist
                if self._old_task is not None:  # Wenn eine alte Aufgabe bereits läuft
                    self._old_task.cancel()  # Bricht die alte Aufgabe ab
                self._old_task = asyncio.create_task(self.task())  # Erstellt eine neue asynchrone Aufgabe aus der aktuellen Aufgabe (self.task) und speichert sie in self._old_task
                self.task = None  # Setzt self.task auf None, um anzuzeigen, dass die Aufgabe ausgeführt wird
            await asyncio.sleep(0.1)  # Wartet 100 ms, bevor die Schleife erneut überprüft, ob eine neue Aufgabe vorhanden ist

    # ↓↓↓↓↓↓↓↓↓↓
    # Die Methode baut die Verbindung zur Drohne auf,
    # informiert über den Start, beginnt die Fortschrittsspeicherung
    # im Hintergrund und startet die Missionsausführung
    # – entweder vollständig oder ab gespeichertem Fortschritt.

    async def _start(self) -> None:  # Interne Methode, die die Haupt-Eventschleife des Missionscomputers startet
        """
        Asynchronous main loop for mission execution and communication.
        """
        await self._comms.connect()  # Stellt die Verbindung zur Drohne her
        await self.status("Mission Computer Started")  # Gibt eine Statusmeldung aus, dass der Missionscomputer gestartet wurde

        asyncio.create_task(self.save_progress())  # Startet die asynchrone Aufgabe zum periodischen Speichern des Fortschritts
        await self.status(f"Starting with Progress: {self.progress}")  # Gibt eine Statusmeldung aus, die den aktuellen Fortschritt anzeigt
        if "action" in self.current_mission_plan.keys():  # Überprüft, ob der aktuelle Missionsplan eine Aktion enthält
            self.running = True  # Setzt das Flag running auf True, um anzuzeigen, dass eine Mission läuft
            plan: dict = self.current_mission_plan  # Setzt den Plan auf den aktuellen Missionsplan
            if self.progress > 0:  # Überprüft, ob der Fortschritt größer als 0 ist
                plan = action_with_count(
                    self.current_mission_plan, self.progress)  # Berechnet den nächsten Aktionsplan basierend auf dem aktuellen Fortschritt
                if isinstance(plan, int):  # Überprüft, ob der Plan ein Integer ist (d. h. keine weitere Aktion vorhanden ist)
                    sp(f"Progress {self.progress} exceeds plan actions, "
                       f"resetting to 0")  # Gibt eine Fehlermeldung aus, dass der Fortschritt die Anzahl der Aktionen im Plan überschreitet
                    self.progress = 0  # Setzt den Fortschritt auf 0 zurück
                    plan = self.current_mission_plan  # Setzt den Plan auf den aktuellen Missionsplan, um von vorne zu beginnen
            if self.main_programm is not None:  # Überprüft, ob bereits ein Hauptprogramm läuft
                self.main_programm.cancel()  # Bricht das laufende Hauptprogramm ab
            self.main_programm = asyncio.create_task(
                self.execute(plan))  # Erstellt eine neue asynchrone Aufgabe, die den Plan ausführt
        else:  # Wenn der aktuelle Missionsplan keine Aktion enthält
            await self.status("No Valid Mision")  # Gibt eine Statusmeldung aus, dass keine gültige Mission vorhanden ist
            sp("Waiting for Networking connection")  # Gibt eine Fehlermeldung aus, dass auf eine Netzwerkverbindung gewartet wird

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode ist ein Callback, z. B. wenn über die Groundstation eine
    # neue Missionsdatei übermittelt wurde. Sie stoppt die aktuelle
    # Mission (falls aktiv), bricht ggf. laufende Tasks ab, setzt die neue
    # Mission auf, und sorgt dafür, dass die Eventschleife sie beim
    # nächsten Zyklus startet.
    
    async def new_mission(self, plan: str) -> None:  # Callback-Methode, die aufgerufen wird, wenn eine neue Missionsdatei empfangen wird
        """
        Callback for receiving a new mission plan.

        :param plan: Path to the new mission plan file.
        :type plan: str
        """
        if self.main_programm:  # Überprüft, ob ein Hauptprogramm läuft
            try:  # Versucht, das laufende Hauptprogramm abzubrechen
                self.main_programm.cancel()  # Bricht das laufende Hauptprogramm ab
            except asyncio.CancelledError:  # Wenn das Abbrechen des Hauptprogramms einen CancelledError auslöst
                sp("Main programm already canceled")  # Gibt eine Fehlermeldung aus, dass das Hauptprogramm bereits abgebrochen wurde
            for task in self.cancel_list:  # Iteriert über die Liste der Tasks, die beim Abbruch der Mission gestoppt werden sollen
                try:  # Versucht, jeden Task in der Liste abzubrechen
                    task()  # Ruft die Stop-Funktion des Tasks auf, um ihn zu beenden
                except Exception as e:  # Wenn ein Fehler beim Abbrechen des Tasks auftritt
                    sp(f"Error in canceling: {e}")  # Gibt eine Fehlermeldung aus, die den Fehler beschreibt
        self.running = False  # Setzt das Flag running auf False, um anzuzeigen, dass keine Mission läuft
        self.initiate(plan)  # Ruft die Methode initiate auf, um den neuen Missionsplan zu laden
        self.task = self._start  # Setzt die aktuelle Aufgabe auf die Methode _start, die die Haupt-Eventschleife startet

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode startet das Kamera-Subsystem der Drohne Sie wird
    # typischerweise innerhalb einer Mission aufgerufen, wenn die Kamera
    # zur Bildaufnahme aktiviert werden soll – z. B. vor einer Analyse oder
    # beim Überfliegen eines Zielgebiets.

    async def start_camera(self, options: dict) -> None:  # Methode zum Starten des Kamera-Subsystems
        """
        Start the camera subsystem.

        :param options: Options for starting the camera (e.g., images per
            second).
        :type options: dict
        """
        await self.status("Starting Camera")  # Gibt eine Statusmeldung aus, dass die Kamera gestartet wird
        self._image.start_cam(options.get("ips", 1))  # Startet die Kamera mit der angegebenen Anzahl von Bildern pro Sekunde (ips), Standardwert ist 1, wenn nicht angegeben

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode stoppt die laufende Kamera und ruft danach eine Methode
    # zur Verarbeitung oder Rückgabe der gefilterten Objekte auf
    # – z. B. erkannte Formen oder Farben aus der Bildanalyse.

    async def stop_camera(self, options: dict) -> None:  # Methode zum Stoppen des Kamera-Subsystems
        """
        Stop the camera subsystem and process filtered objects.

        :param options: Options for stopping the camera.
        :type options: dict
        """
        await self.status("Stopping Camera")  # Gibt eine Statusmeldung aus, dass die Kamera gestoppt wird. await bezeichnet, dass die Methode asynchron ist und auf die Beendigung der Kamera warten kann.
        self._image.stop_cam()  # Stoppt die Kamera, um die Bildaufnahme zu beenden
        self._image.get_filtered_objs()  # Ruft die Methode auf, um die gefilterten Objekte zu verarbeiten oder zurückzugeben

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode befiehlt der Drohne den Startvorgang bis auf eine
    # definierte Höhe. Die Zielhöhe wird aus den übergebenen
    # Optionen entnommen – oder, falls nicht vorhanden,
    # aus den Missionsparametern. Anschließend wird der Befehl
    # an das Kommunikationsmodul weitergegeben.

    async def takeoff(self, options: dict) -> None:  # Methode zum Starten der Drohne
        """
        Command the drone to take off to a specified height.

        :param options: Options containing the target height.
        :type options: dict
        """
        h: float = options.get(
            "height", self.current_mission_plan["parameter"].get(
                "flight_height", 5))  # Extrahiert die Zielhöhe aus den übergebenen Optionen oder aus den Missionsparametern, Standardwert ist 5, wenn nicht angegeben
        await self.status(f"Taking Off to height {h}")  # Gibt eine Statusmeldung aus, dass die Drohne auf die angegebene Höhe startet
        await self._comms.start(h)  # Startet die Drohne auf die angegebene Höhe, indem der Befehl an das Kommunikationsmodul weitergegeben wird

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode steuert die Landung der Drohne.
    # Sie kann:
    # ohne Zielangabe an der aktuellen Position landen,
    # mit Koordinaten zu einem bestimmten Ziel fliegen und dort landen,
    # mit Farberkennung (optional mit Form) ein Objekt suchen und die Drohne gezielt darüber positionieren, bevor sie landet.

    async def land(self, objective: dict) -> None:  # Methode zum Landen der Drohne
        """
        Land the drone at a specified location, optionally using color/shape
        detection.

        :param objective: Dictionary with landing coordinates and optional
            color/shape.
        :type objective: dict
        """
        if "lat" not in objective.keys() or "lon" not in objective.keys():  # Überprüft, ob die Zielkoordinaten (Latitude und Longitude) im übergebenen Dictionary vorhanden sind
            await self.status(
                "No landing position given, landing at current position")  # Gibt eine Statusmeldung aus, dass keine Zielkoordinaten angegeben wurden und die Drohne an der aktuellen Position landet
            await self._comms.mov_by_vel(
                [0, 0, self.config.get("land_speed", 2)])  # Bewegt die Drohne mit der angegebenen Landegeschwindigkeit (Standardwert ist 2, wenn nicht angegeben) an die aktuelle Position
            await self._comms.landed()  # Führt die Landung der Drohne aus
            return  # Beendet die Methode, da die Drohne an der aktuellen Position gelandet ist

        sp(f"Landing at {objective['lat']:.6f} {objective['lon']:.6f}")  # Gibt eine Statusmeldung aus, die die Zielkoordinaten für die Landung anzeigt
        if not (await self._comms.is_flying()):  # Überprüft, ob die Drohne gerade fliegt
            return  # Beendet die Methode, wenn die Drohne nicht fliegt, da sie nicht landen kann
        await self.mov(options=objective)  # Bewegt die Drohne zu den angegebenen Zielkoordinaten, um dort zu landen

        if "color" not in objective.keys():  # Überprüft, ob eine Farbe im übergebenen Dictionary angegeben ist
            sp("No color given")  # Gibt eine Statusmeldung aus, dass keine Farbe angegeben wurde
            await self._comms.mov_by_vel(
                [0, 0, self.config.get("land_speed", 2)])  # Bewegt die Drohne mit der angegebenen Landegeschwindigkeit (Standardwert ist 2, wenn nicht angegeben) an die Zielposition
            return  # Beendet die Methode, da keine Farberkennung erforderlich ist

        sp(f"Suche Objekt vom Typ '{objective.get('shape', None)}' "
           f"mit Farbe '{objective['color']}'")  # Gibt eine Statusmeldung aus, die die gesuchte Farbe und optional die Form des Objekts anzeigt

        min_alt: float = 1  # Mindesthöhe, auf der die Drohne landen soll
        detected_alt: float = await self._comms.get_relative_height()  # Ruft die aktuelle relative Höhe der Drohne ab

        # Loop to adjust position until the drone is close enough to the object
        while detected_alt > min_alt:  # Solange die Drohne höher als die Mindesthöhe ist
            offset, detected_alt, yaw = \
                await self._image.get_current_offset_closest(
                    objective["color"], objective.get('shape', None))  # Ruft die aktuelle Position des Objekts basierend auf der Farbe und optional der Form ab

            if offset is None:  # Wenn kein Objekt gefunden wurde
                await self.status("Objekt nicht gefunden.")  # Gibt eine Statusmeldung aus, dass das Objekt nicht gefunden wurde
                break  # Beendet die Schleife, da kein Objekt gefunden wurde

            vel_ver: float = 1 / diag(offset[0], offset[1])  # Berechnet die vertikale Geschwindigkeit basierend auf der Diagonale des Offsets
            if vel_ver/2 > detected_alt:  # Wenn die vertikale Geschwindigkeit halbiert größer als die aktuelle Höhe ist
                vel_ver = detected_alt / 2  # Setzt die vertikale Geschwindigkeit auf die Hälfte der aktuellen Höhe, um ein sicheres Landen zu gewährleisten
            await self._comms.mov_by_vel(
                [offset[0]/10, offset[1]/10, vel_ver], yaw)  # Bewegt die Drohne in Richtung des Offsets mit der berechneten vertikalen Geschwindigkeit und optionalem Yaw-Winkel

            await asyncio.sleep(0.1)  # Wartet 100 ms, bevor die nächste Iteration der Schleife gestartet wird

        await self.status("Landeposition erreicht. Drohne landet.")  # Gibt eine Statusmeldung aus, dass die Landeposition erreicht wurde und die Drohne landet
        await self._comms.mov_by_vel(
            [0, 0, self.config.get("land_speed", 2)])  # Bewegt die Drohne mit der angegebenen Landegeschwindigkeit (Standardwert ist 2, wenn nicht angegeben) an die Landeposition
        await self._comms.landed()  # Führt die Landung der Drohne aus

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode pausiert die Missionsausführung für eine definierte
    # Anzahl an Sekunden. Sie wird z. B. verwendet, um der Drohne Zeit
    # zu geben, etwas zu stabilisieren, eine Kamera abkühlen zu lassen oder
    # einfach einen Ablauf zu verzögern.

    async def delay(self, options: dict) -> None:  # Methode zum Verzögern der Ausführung für eine bestimmte Zeit
        """
        Delay execution for a specified amount of time.

        :param options: Dictionary with the delay time in seconds.
        :type options: dict
        """
        sp(f"Delay: {options.get('time', 1)}")  # Gibt eine Statusmeldung aus, die die Verzögerungszeit anzeigt
        await asyncio.sleep(options.get("time", 1))  # Wartet die angegebene Verzögerungszeit in Sekunden, Standardwert ist 1 Sekunde, wenn nicht angegeben

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode erhält eine Liste von Missionsaktionen
    # (z. B. takeoff, delay, mov, land) und führt sie nacheinander aus
    # – genau so, wie sie in der Liste stehen.
    # Das ist nützlich für strukturierte Missionsabschnitte oder
    # Unterprogramme innerhalb eines größeren Missionsplans.
    
    async def execute_list(self, options: List[dict]) -> None:  # Methode zum Ausführen einer Liste von Aktionen aus dem Missionsplan
        """
        Execute a list of actions sequentially.

        :param options: List of action dictionaries.
        :type options: List[dict]
        """
        for item in options:  # Iteriert über die Liste der Aktionen
            await self.execute(item)  # Führt jede Aktion in der Liste aus

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode bewegt die Drohne mehrfach nacheinander zu verschiedenen
    # GPS-Koordinaten (bzw. Bewegungszielen), basierend auf einer Liste von
    # Bewegungsanweisungen. Jede Bewegung wird mit mov() ausgeführt,
    # und der Fortschritt wird nach jedem Schritt erhöht.

    async def mov_multiple(self, options: List[dict]) -> None:  # Methode zum Bewegen der Drohne zu mehreren Positionen nacheinander
        """
        Move to multiple locations sequentially.

        :param options: List of movement command dictionaries.
        :type options: List[dict]
        """
        await self.status(f"Moving Multiple {len(options)}")  # Gibt eine Statusmeldung aus, die die Anzahl der Bewegungsziele anzeigt
        for item in options:  # Iteriert über die Liste der Bewegungsanweisungen
            await self.mov(item)  # Bewegt die Drohne zu jeder Position in der Liste
            self.progress += 1  # Erhöht den Fortschritt um 1 nach jeder Bewegung

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode bewegt die Drohne zu einer bestimmten
    # GPS-Position (Latitude, Longitude) in einer bestimmten Höhe
    # – optional auch mit einer definierten Yaw-Ausrichtung (Rotation).
    # Wenn die Drohne noch nicht fliegt, wird automatisch gestartet.

    async def mov(self, options: dict) -> None:  # Methode zum Bewegen der Drohne zu einer bestimmten GPS-Position
        """
        Move the drone to a specified latitude, longitude, and height.

        :param options: Dictionary with 'lat', 'lon', and optional 'height' and
            'yaw'.
        :type options: dict
        """
        await self.status(
            f"Moving to {options['lat']:.6f} {options['lon']:.6f}")  # Gibt eine Statusmeldung aus, die die Zielkoordinaten anzeigt
        yaw: Optional[float] = options.get("yaw")  # Extrahiert den Yaw-Winkel aus den übergebenen Optionen, Standardwert ist None, wenn nicht angegeben
        if "height" in options.keys():  # Überprüft, ob eine Höhe in den übergebenen Optionen angegeben ist
            h: float = options["height"]  # Setzt die Höhe auf den angegebenen Wert
        else:  # Wenn keine Höhe angegeben ist
            h: float = self.current_mission_plan.get(
                "parameter", {}).get("height", 5)  # Setzt die Höhe auf den Wert aus den Missionsparametern oder auf 5, wenn nicht angegeben
        pos: List[float] = [options['lat'], options['lon'], h]  # Erstellt eine Liste mit den Zielkoordinaten (Latitude, Longitude, Höhe)
        if not await self._comms.is_flying():  # Überprüft, ob die Drohne gerade fliegt
            await self._comms.start(h)  # Startet die Drohne auf die angegebene Höhe, wenn sie nicht fliegt

        await self._comms.mov_to_lat_lon_alt(pos, yaw)  # Bewegt die Drohne zu den angegebenen GPS-Koordinaten und optionalem Yaw-Winkel

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode startet eine Endlosschleife, in der alle 2 Sekunden
    # gewartet wird. Sie blockiert absichtlich die weitere Missionsausführung
    # und wird daher nur in Ausnahmefällen eingesetzt
    # (z. B. um dauerhaft in einen Wartezustand zu gehen).

    async def forever(self, options: dict) -> None:  # Methode, die eine Endlosschleife startet
        """
        Run an infinite loop (used for testing or waiting).

        :param options: Options dictionary (unused).
        :type options: dict
        """
        sp("Running Until Forever")  # Gibt eine Statusmeldung aus, dass die Endlosschleife gestartet wurde
        while True:  # Endlosschleife, die ständig läuft
            await asyncio.sleep(2)  # Wartet 2 Sekunden, bevor die Schleife erneut ausgeführt wird

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode:
    # Holt sich alle zuvor erkannten Objekte (z. B. aus Kamerabildern),
    # berechnet eine Route durch alle Ziele (optimiert),
    # fliegt jedes Ziel einzeln an,
    # wartet ggf. kurz,
    # und macht an jedem Ziel ein Bild.

    async def mov_to_objects_cap_pic(self, options: dict) -> None:  # Methode zum Bewegen der Drohne zu erkannten Objekten und Aufnehmen von Bildern
        """
        Move to detected objects and capture images at each location.

        :param options: Dictionary with movement and delay options.
        :type options: dict
        """
        sp("Moving to objects and taking picture")  # Gibt eine Statusmeldung aus, dass die Drohne zu erkannten Objekten bewegt wird und Bilder aufgenommen werden
        obj: List[dict] = self._image.get_filtered_objs()  # Ruft die Liste der erkannten Objekte aus dem Kamera-Subsystem ab
        path: List[Any] = find_shortest_path(
            obj, await self._comms.get_position_lat_lon_alt())  # Berechnet den kürzesten Pfad zu den erkannten Objekten basierend auf der aktuellen Position der Drohne
        if "height" in options.keys():  # Überprüft, ob eine Höhe in den übergebenen Optionen angegeben ist
            h: float = options["height"]  # Setzt die Höhe auf den angegebenen Wert
        else:  # Wenn keine Höhe angegeben ist
            h: float = self.current_mission_plan.get(
                "parameter", {}).get("height", 5)  # Setzt die Höhe auf den Wert aus den Missionsparametern oder auf 5, wenn nicht angegeben

        for i, item in enumerate(path):  # Iteriert über die Liste der erkannten Objekte und deren Positionen
            sp(f"Moving to {i+1}/{len(path)}: {item}")  # Gibt eine Statusmeldung aus, die die aktuelle Position und die Gesamtanzahl der erkannten Objekte anzeigt
            await self.mov({"lat": item[0], "lon": item[1], "height": h})  # Bewegt die Drohne zu der aktuellen Position des erkannten Objekts mit der angegebenen Höhe
            await asyncio.sleep(options.get("delay", 0.5))  # Wartet die angegebene Verzögerungszeit (Standardwert ist 0,5 Sekunden, wenn nicht angegeben)
            await self._image.take_image()  # Nimmt ein Bild mit der Kamera auf, nachdem die Drohne zu dem erkannten Objekt bewegt wurde

    # ↓↓↓↓↓↓↓↓↓↓
    # Diese Methode gibt eine Statusmeldung sowohl:
    # lokal per smart_print (zur Konsole oder ins Log) und
    # extern an die Kommunikationsschnittstelle (z. B. zur Groundstation).

    async def status(self, msg: str) -> None:  # Methode zum Senden einer Statusmeldung
        """
        Send a status message to the communication subsystem.

        :param msg: Status message to send.
        :type msg: str
        """
        sp(msg)  # Gibt die Statusmeldung lokal aus, z. B. in der Konsole oder im Log
        await self._comms.send_status(msg)  # Sendet die Statusmeldung an die Kommunikationsschnittstelle, z. B. zur Groundstation
