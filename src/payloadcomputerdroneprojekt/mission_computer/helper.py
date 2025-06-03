import math  # Importiert das math-Modul, mit dem mathematische Funktionen wie Quadratwurzel (math.sqrt) oder trigonometrische Funktionen verwendet werden können.
import os  # Importiert das os-Modul, mit dem man Dateipfade prüfen, Dateien löschen, Verzeichnisse erstellen usw. kann. Wird typischerweise z. B. für os.path.exists() oder os.remove() verwendet.
import json  # Importiert das json-Modul, mit dem JSON-Daten verarbeitet werden können. Wird typischerweise z. B. für json.load() oder json.dump() verwendet.
from payloadcomputerdroneprojekt.helper \
    import smart_print as sp  # Importiert die Funktion smart_print aus dem Modul payloadcomputerdroneprojekt.helper. Diese Funktion wird verwendet, um Nachrichten auf der Konsole auszugeben, möglicherweise mit zusätzlicher Formatierung oder Logik.


# ↓↓↓↓↓↓↓↓↓↓
# Diese Funktion nimmt:
# eine Liste von Objekten mit Positionen (objs),
# und eine Startposition (start),
# und gibt eine Liste von Objektpositionen zurück, sortiert nach der
# Manhattan-Distanz zum Startpunkt.
# Sie wird z. B. in mov_to_objects_cap_pic() verwendet.

def find_shortest_path(objs: list[dict], start: list[float]
                       ) -> list[list[float]]:  # Definiert die Funktion. objs: Liste von Objekten, z. B. [{"pos": [48.123, 11.456]}, {...}]; start: Startpunkt, z. B. [48.120, 11.450]; Rückgabe: Liste von Positionen [[lat, lon], ...] sortiert nach Distanz zum Start
    """
    Find the shortest path to all objects from a starting point.

    The function sorts the positions of the objects based on their Manhattan
    distance from the starting point and returns the sorted list of positions.

    :param objs: List of objects, each with a "pos" key containing coordinates.
    :type objs: list[dict]
    :param start: Starting position as [x, y].
    :type start: list[float]
    :return: Sorted list of positions based on distance from start.
    :rtype: list[list[float]]
    """
    if len(objs) == 0:  # überprüft, ob die Liste objs leer ist
        return []  # Wenn ja, gibt eine leere Liste zurück
    path = []  # Initialisiert eine leere Liste, um die Positionen zu speichern
    for obj in objs:  # Iteriert über jedes Objekt in der Liste objs
        path.append(obj["pos"])  # Fügt die Position des Objekts (obj["pos"]) zur Liste path hinzu
    # Sort positions by Manhattan distance from the start
    path.sort(key=lambda x: abs(x[0] - start[0]) + abs(x[1] - start[1]))  # Sortiert die Liste path basierend auf der Manhattan-Distanz zum Startpunkt
    return path  # Gibt die sortierte Liste der Positionen zurück


# ↓↓↓↓↓↓↓↓↓↓
# Diese Funktion zählt rekursiv, wie viele Einzelaktionen in einem
# Missionsplan enthalten sind.
# Sie berücksichtigt dabei Sonderaktionen wie:
# "list": verschachtelte Aktionsgruppen
# "mov_multiple": Liste von Bewegungen
# Sie wird z. B. in initiate() verwendet, um max_progress zu bestimmen

def count_actions(actions: dict) -> int:  # Definiert die Funktion. actions: Ein Aktionsplan, z. B. {"action": "list", "commands": [{"action": "mov", ...}, {...}]}
    """
    Recursively count the number of actions in a nested action plan.

    :param actions: Action plan dictionary.
    :type actions: dict
    :return: Total number of actions.
    :rtype: int
    """
    if actions["action"] == "list":  # Überprüft, ob die Aktion eine Liste ist
        c = 0  # Initialisiert einen Zähler c auf 0
        for item in actions["commands"]:  # Iteriert über alle Befehle in der Liste
            c += count_actions(item)  # Ruft die Funktion rekursiv auf, um die Anzahl der Aktionen in jedem Befehl zu zählen und addiert sie zu c
        return c  # Gibt die Gesamtanzahl der Aktionen zurück
    elif actions["action"] == "mov_multiple":  # Überprüft, ob die Aktion eine Mehrfachbewegung ist
        return len(actions["commands"])  # Gibt die Anzahl der Bewegungen in der Liste zurück
    return 1  # Für alle anderen Aktionen wird 1 zurückgegeben, da es sich um eine einzelne Aktion handelt


# ↓↓↓↓↓↓↓↓↓↓
# Diese Funktion erhält:
# einen vollständigen Missionsplan (plan)
# und eine Anzahl von Schritten, die bereits abgeschlossen sind (count),
# und gibt dann den verbleibenden Plan ab dem nächsten offenen Schritt zurück.

def action_with_count(plan: dict, count: int):  # Definiert die Funktion. plan: Ein Aktionsplan, z. B. {"action": "list", "commands": [{"action": "mov", ...}, {...}]}; count: Anzahl der bereits abgeschlossenen Schritte, z. B. 2
    """
    Find the next action in the plan and return it with the updated count.

    If the count is 0, returns the plan as is.
    If the count exceeds the number of actions, returns the remaining count.

    :param plan: The action plan.
    :type plan: dict
    :param count: Number of actions to skip.
    :type count: int
    :return: The next action or the remaining count.
    :rtype: dict or int
    """
    if plan["action"] == "list":  # Überprüft, ob die Aktion eine Liste ist
        for i, item in enumerate(plan["commands"]):  # Iteriert über alle Befehle in der Liste und deren Indizes
            ret = action_with_count(item, count)  # Ruft die Funktion rekursiv auf, um die nächste Aktion zu finden
            if not isinstance(ret, int):  # Überprüft, ob die Rückgabe kein Integer ist (d.h. es ist eine Aktion)
                # Found the next action, return the updated plan
                return {
                    "action": "list",
                    "commands": [ret] + plan["commands"][i+1:]
                }  # Gibt den Plan mit der gefundenen Aktion und den verbleibenden Befehlen zurück
            count = ret  # Aktualisiert den Zähler count mit der verbleibenden Anzahl von Schritten
    elif plan["action"] == "mov_multiple":  # Überprüft, ob die Aktion eine Mehrfachbewegung ist
        if count < len(plan["commands"]):  # Überprüft, ob der Zähler count kleiner ist als die Anzahl der Befehle in der Liste
            # Return the remaining commands after skipping 'count' actions
            return {
                "action": "mov_multiple",
                "commands": plan["commands"][count:]
            }  # Gibt die verbleibenden Befehle zurück, nachdem 'count' Aktionen übersprungen wurden
        else:  # Wenn count größer oder gleich der Anzahl der Befehle ist
            return count - len(plan["commands"])  # Gibt die verbleibende Anzahl der Schritte zurück, nachdem alle Befehle ausgeführt wurden

    if count == 0:  # Überprüft, ob count gleich 0 ist
        return plan  # Gibt den Plan zurück, wenn keine Schritte übersprungen werden sollen
    return count - 1  # Reduziert den Zähler count um 1 und gibt ihn zurück, wenn eine einzelne Aktion ausgeführt wird


# ↓↓↓↓↓↓↓↓↓↓
# Diese Funktion prüft, ob ein Missionsobjekt (Dictionary oder Liste)
# einen Eintrag "src" enthält. Falls ja, wird die darin angegebene
# Datei geladen, und die Inhalte ("action" & "commands") werden übernommen
# – ggf. rekursiv.

def rec_serialize(obj):  # Definiert die Funktion. obj: Ein Objekt, das ein Dictionary oder eine Liste sein kann, z. B. {"src": "commands.json", "action": "mov", "commands": [...]}
    """
    Recursively serialize the object to load commands from a file if specified.

    If the object is a dictionary and contains a "src" key, it loads the
    commands from the specified file and updates the object. If the object is a
    list, it recursively serializes each element.

    :param obj: The object to serialize, which can be a dictionary or a list.
    :type obj: dict or list
    """
    if isinstance(obj, dict):  # Überprüft, ob obj ein Dictionary ist
        if "src" in obj.keys():  # Überprüft, ob das Dictionary den Schlüssel "src" enthält
            if os.path.exists(obj["src"]):  # Überprüft, ob die Datei existiert
                with open(obj["src"], "r") as f:  # Öffnet die Datei im Lesemodus
                    subobj = json.load(f)  # Lädt den Inhalt der Datei als JSON-Objekt
                    obj["action"] = subobj["action"]  # Übernimmt die Aktion aus dem geladenen Objekt
                    obj["commands"] = subobj["commands"]  # Übernimmt die Befehle aus dem geladenen Objekt
                    # Recursively serialize the loaded commands
                    rec_serialize(subobj["commands"])  # Ruft die Funktion rekursiv auf, um alle Befehle zu serialisieren
            else:  # Wenn die Datei nicht existiert
                sp(f"File {obj['src']} not found")  # Gibt eine Fehlermeldung aus
    elif isinstance(obj, list):  # Überprüft, ob obj eine Liste ist
        # Recursively serialize each element in the list
        [rec_serialize(i) for i in obj]  # Ruft die Funktion rekursiv für jedes Element in der Liste auf


# ↓↓↓↓↓↓↓↓↓↓
# Die Funktion berechnet die euklidische Distanz (auch Luftlinie genannt)
# vom Ursprung (0,0) zu einem Punkt (x, y):

def diag(x: float, y: float) -> float:  # Definiert die Funktion. x: X-Koordinate, y: Y-Koordinate; Rückgabe: euklidische Distanz als float
    """
    Calculate the Euclidean distance from the origin to the point (x, y).

    :param x: X coordinate.
    :type x: float
    :param y: Y coordinate.
    :type y: float
    :return: Euclidean distance.
    :rtype: float
    """
    return math.sqrt(x**2 + y**2)  # Berechnet die euklidische Distanz mit der Formel: sqrt(x^2 + y^2)
