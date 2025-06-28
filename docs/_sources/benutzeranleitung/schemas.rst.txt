.. _schemas:

Schema
======

In diesem Abschnitt werden die json Schema dokumentiert, die im Payload
Computer Drone Projekt verwendet werden. Diese Schema definieren die Struktur
und Validierung der Daten, die zwischen den verschiedenen Komponenten des
Systems ausgetauscht werden.


Einleitung
=================

JSON Schema ist ein standardisiertes Format zur Definition der Struktur, Datentypen und Validierungsregeln von JSON-Dokumenten.  
Mit einem Schema lassen sich Konfigurations- oder Missionsdateien maschinell prüfen und zugleich für Entwickler und Anwender klar dokumentieren.  
Dieses Dokument beschreibt in genereller Form:

- Aufbau eines JSON-Schema (Root-Objekt, `properties`, `definitions` usw.)  
- Typisierung und Constraints (z. B. `type`, `minimum`, `required`)  
- Erweiterungsmechanismen über `$ref` und `additionalProperties`  
- Best Practices für Versionierung, Validierung und Integration in Workflows  

Hier finden Sie eine Übersicht und Beschreibung der relevanten Schema, die im Projekt verwendet werden. Details zu jedem Schema finden Sie in den jeweiligen Unterabschnitten.


Config-Schema
=================

Das Config-Schema definiert die Struktur der Konfigurationsdateien, die für die Initialisierung und Anpassung des Systems verwendet werden. Es legt fest, welche Parameter erforderlich sind und welche optional sein können.
Die Datei config-schema.json dient als Schema zur Validierung von Konfigurationsdateien in JSON-Format. Sie definiert die zulässigen Schlüssel, Datentypen und mögliche Werte, um eine konsistente und fehlerfreie Konfiguration sicherzustellen
und zu ermöglichen, dass das System korrekt funktioniert. Dieses Schema ist entscheidend für die korrekte Initialisierung und Anpassung des Systems an spezifische Anforderungen und Umgebungen.
Das Schema stellt sicher, dass alle erforderlichen Parameter vorhanden sind und die richtigen Datentypen verwendet werden. Es hilft auch, mögliche Fehler in der Konfiguration frühzeitig zu erkennen und zu beheben, bevor sie zu Problemen im Betrieb führen können.


Die Datei config-schema.json ist im Verzeichnis `src/payload_computer/schemas/` zu finden.

Schema-Struktur (Root-Ebene)
----------------------------
Root-Objekt (Typ ``object``) mit genau fünf Properties.  
Zusätzliche Felder sind nicht erlaubt (``additionalProperties: false``).

+-------------------+---------+------------------------------------------------------+--------------+
| Property          | Typ     | Beschreibung                                          | Pflichtfeld? |
+===================+=========+======================================================+==============+
| image             | object  | Bildanalyse-Parameter                                 | ja           |
+-------------------+---------+------------------------------------------------------+--------------+
| camera            | object  | Kameraspezifische Parameter                           | ja           |
+-------------------+---------+------------------------------------------------------+--------------+
| mission_computer  | object  | Einstellungen der Missions-Computer-Logik             | ja           |
+-------------------+---------+------------------------------------------------------+--------------+
| communications    | object  | Kommunikations- und Fehler-Toleranzwerte              | ja           |
+-------------------+---------+------------------------------------------------------+--------------+
| mission_storage   | string  | Arbeitsverzeichnis der Missions-Daten                 | ja           |
+-------------------+---------+------------------------------------------------------+--------------+

Details zu den Objekten
------------------------

1. Image-Einstellungen (``image``)
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   Felder in ``image``:

   - **fov** (array of 2 numbers, optional)  
     Blickfeld in Grad \[horizontal, vertikal\], Werte zwischen 0 und 180.

   - **path** (string, optional, default: `"data/images"`)  
     Verzeichnis für Bilddateien.

   - **colors** (array, required, minLength: 1)  
     Liste von Farb-Objekten. Jedes Element muss *entweder*  
       - **name** (string, required),  
         **upper** (HSV triple) und **lower** (HSV triple)  
     *oder*  
       - **name** (string, required),  
         **upper_0**, **lower_0**, **upper_1**, **lower_1** (je HSV-triple)  
     enthalten.

   - **shape_color** (object, required)  
     HSV-Grenzwerte für die Form-Erkennung:

     - **upper** (HSV triple)  
     - **lower** (HSV triple)

   - **threashold** (number, required, default: -1, minimum: -1)  
     Grauwert-Schwellwert.

   - **min_diagonal_code_element** (number, optional, default: 1)  
     Minimale Diagonale eines Code-Elements [m].

   - **min_diagonal_shape** (number, optional, default: 1)  
     Minimale Diagonale einer Form [m].

   - **min_diagonal** (number, required, default: 10)  
     Minimale Diagonale eines beliebigen Objekts [m].

   - **camera_offset** (array of 3 numbers, optional, default: [0,0,0])  
     Physische Versetzung der Kamera \[m\].

   - **rotation_offset** (array of 3 numbers, optional, default: [0,0,0], range: -360..360)  
     Rotations-Offset um X/Y/Z in Grad.

   - **distance_objs** (number, optional, default: 5, minimum: 0)  
     Distanz [m], ab der Objekte als identisch gelten.

   - **length_code_side** (number, optional, default: 0.5)  
     Kantenlänge eines Code-Elements [m].

   - **length_box_short_side** (number, optional, default: 0.4)  
     kurze Seitenlänge einer Box [m].

   - **length_box_long_side** (number, optional, default: 0.6)  
     lange Seitenlänge einer Box [m].

   - **strong_bounding_check** (boolean, optional, default: true)  
     Bounding-Box muss quadratisch sein.

   - **bounding_box_shrink_percentage** (number, optional, default: 0, range: 0..1)  
     Prozentsatz zur Verkleinerung der BB vor Messung.

   - **approx_poly_epsilon** (number, optional, default: 0.04, minimum: 0)  
     Genauigkeit der Polygon-Approximation.

   - **min_shape_area** (number, optional, default: 10000, minimum: 0)  
     Minimale Fläche einer Form in Pixel.

   **Definition: HSV-Triple**  
   Ein Array aus drei Integern:
   1. Hue: –5 .. 100  
   2. Saturation: –128 .. 128  
   3. Value: –128 .. 128

2. Kamera-Parameter (``camera``)
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   - **main** (object, required)  
     - **format** (string) z. B. `"XRGB8888"`  
     - **size** (array of 2 integers ≥0) \[Breite, Höhe\]

   - **control** (object, required)  
     - **ExposureTime** (integer ≥30)  
       Belichtungszeit in Millisekunden.

3. Missions-Computer (``mission_computer``)
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   - **recouver_time** (number ≥0, default: 10)  
     Zeit [s] für Neustart nach Crash bis Missionsabbruch.

   - **land_speed** (number ≥0.1, default: 2)  
     Lande­geschwindigkeit [m/s].

   - **indoor** (boolean, default: false)  
     Indoor-Flugmodus aktiv?

4. Kommunikation (``communications``)
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   - **allowed_arm** (boolean, default: false)  
     Motor-Freigabe erlaubt?

   - **allowed_disarm** (boolean, default: false)  
     Motor-Sperre erlaubt?

   - **allowed_mode_switch** (boolean, default: true)  
     Flugmodus-Wechsel erlaubt?

   - **pos_error** (number, default: 0.75)  
     Positions-Toleranz.

   - **vel_error** (number, default: 0.5)  
     Geschwindigkeits-Toleranz.

   - **degree_error** (number, default: 0.5)  
     Winkel-Toleranz.

5. Missions-Speicherort (``mission_storage``)
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   - **mission_storage** (string, required, default: `"mission_storage"`)  
     Arbeitsverzeichnis der Missionsdaten.

Beispiel einer gültigen Konfiguration
-------------------------------------

.. code-block:: json

   {
     "image": {
       "fov": [90, 60],
       "path": "data/images",
       "colors": [
         {
           "name": "rot",
           "upper": [10, 128, 128],
           "lower": [0, 128, 128]
         },
         {
           "name": "blau",
           "upper_0": [100, 100, 100],
           "lower_0": [90, 50, 50],
           "upper_1": [130, 255, 255],
           "lower_1": [110, 100, 100]
         }
       ],
       "shape_color": {
         "upper": [50, 128, 128],
         "lower": [30, 128, 128]
       },
       "threashold": -1,
       "min_diagonal": 15
     },
     "camera": {
       "main": {
         "format": "XRGB8888",
         "size": [640, 480]
       },
       "control": {
         "ExposureTime": 50
       }
     },
     "mission_computer": {
       "recouver_time": 8,
       "land_speed": 1.5,
       "indoor": true
     },
     "communications": {
       "allowed_arm": true,
       "allowed_disarm": false,
       "allowed_mode_switch": true,
       "pos_error": 0.5,
       "vel_error": 0.4,
       "degree_error": 0.2
     },
     "mission_storage": "mission_data"
   }


Mission-Schema
=================

Dieses Dokument beschreibt die Missionskonfiguration für Team Blau's Drohnenprojekt anhand des JSON-Schemas. Das Schema ermöglicht eine strukturierte Definition von Parametern, Aktionen und Befehlen für die Drohne.
Das JSON-Schema besteht aus mehreren Hauptelementen:
- Parameter: Definiert die Flugbedingungen (z. B. Flughöhe).
- Aktionen: Gibt den Typ der Mission an (z. B. "list" oder "mov_multiple").
- Befehle: Enthält spezifische Bewegungs- und Steuerungskommandos
- Bewegungsbefehle: Definiert die Bewegungsrichtung und Geschwindigkeit der Drohne.
- Steuerbefehle: Enthält Befehle zur Steuerung der Drohne, wie Start, Stopp und Notlandung.
Die Datei mission-schema.json ist im Verzeichnis `src/payload_computer/schemas/` zu finden.


Schema-Struktur (Root-Ebene)
----------------------------
Root-Objekt (Typ ``object``). Zusätzliche Felder sind nicht erlaubt (``additionalProperties: false``).

+-------------+---------+------------------------------------------------------+--------------+
| Property    | Typ     | Beschreibung                                          | Pflichtfeld? |
+=============+=========+======================================================+==============+
| parameter   | object  | Missions-Parameter (Höhen etc.)                       | ja           |
+-------------+---------+------------------------------------------------------+--------------+
| action      | string  | Typ der Mission (``list`` oder ``mov_multiple``)      | ja           |
+-------------+---------+------------------------------------------------------+--------------+
| commands    | array   | Liste von Befehlen (siehe Definitionen)               | ja           |
+-------------+---------+------------------------------------------------------+--------------+
| $schema     | string  | Versions-URI des Schemas                              | nein         |
+-------------+---------+------------------------------------------------------+--------------+

Details zu den Root-Properties
------------------------------

parameter (object)
^^^^^^^^^^^^^^^^^^
.. code-block:: json

   "parameter": {
     "flight_height": 5,
     "decision_height": 1
   }

- **flight_height** (number, ≥0)  
  Höhe des Fluges in Metern. *Pflichtfeld*.

- **decision_height** (number, ≥0, default: 1)  
  Höhe, bei der Entscheidungen getroffen werden.

action (string)
^^^^^^^^^^^^^^
- Werte: ``"list"`` oder ``"mov_multiple"``  
- Definiert das Missionsformat.

commands (array)
^^^^^^^^^^^^^^^^
Liste von Befehls-Objekten. Jedes Element muss einem der folgenden Definitionstypen entsprechen:
- ``#/definitions/command``
- ``#/definitions/movement``

Beispiel:
.. code-block:: json

   "commands": [
     { "action": "takeoff", "commands": { "time": 3 } },
     { "lat": 48.766, "lon": 11.423, "height": 5 }
   ]

$schema (string)
^^^^^^^^^^^^^^^^
- Versions-URI, z. B.  
  ``"http://json-schema.org/draft-07/schema#"``.

Definitionen
------------

1. command
   ^^^^^^^

   Ein Union‐Typ (``anyOf``) aus vier möglichen Objekten:

   a) **Verschachtelte Listen** (``action: "list"`` oder ``"mov_multiple"``)  
      - **action**: ``"list"`` oder ``"mov_multiple"``  
      - **commands**: Array von weiteren ``command``-Definitionen  

   b) **Einzelne Bewegung** (``action: "mov_multiple"``)  
      - **action**: ``"mov_multiple"``  
      - **commands**: Ein einziges ``movement``-Objekt  

   c) **Einfache Aktionen**  
      - **action**: einer von  
        ``"start_camera"``, ``"stop_camera"``, ``"takeoff"``, ``"land_at"``,  
        ``"delay"``, ``"forever"``, ``"mov_to_objects_cap_pic"``  
      - **commands**: Objekt mit Aktionseigenschaften (siehe *action_properties*)  

   d) **Lokale Bewegung** (``action: "mov_local"``)  
      - **action**: ``"mov_local"``  
      - **commands**: Objekt mit Koordinaten- und Delta-Felder:  
        - **x, y, z, yaw** (absolute Position/Orientierung)  
        - oder **dx, dy, dz, dyaw** (relative Änderung)  
        - Mindestens: ``x & y`` oder ``dx & dy``.

2. action_properties
   ^^^^^^^^^^^^^^^^^^
   Eigenschaften für einfache Aktionen:

   - **time** (number, ≥0)  
     Dauer in Sekunden.

   - **delay** (number, ≥0)  
     Wartezeit bis Ausführung.

   - **altitude** (number, ≥0)  
     Flughöhe in Metern.

   - **lat**, **lon** (number)  
     GPS-Koordinaten.

   - **ips** (number)  
     Bilder pro Sekunde (z. B. 1, 0.5, 5).

   - **color**, **shape** (string)  
     Filter- oder Erkennungsparameter.

3. movement
   ^^^^^^^^^
   Array von Positions-Objekten:

   - **lat**, **lon** (number) *Pflicht*  
   - **height** (number)  
   - **yaw** (number)  

Beispiel für alle Definitionen
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: json

   "commands": [
     {
       "action": "list",
       "commands": [
         { "action": "takeoff", "commands": { "time": 4 } },
         {
           "action": "mov_local",
           "commands": { "dx": 5, "dy": 0 }
         }
       ]
     },
     [
       { "lat": 48.766, "lon": 11.423, "height": 5, "yaw": 90 }
     ]
   ]

Beispiel einer vollständigen Missions-Config
-------------------------------------------

.. code-block:: json

   {
     "$schema": "https://raw.githubusercontent.com/KonstantinDege/schemas/refs/heads/main/mission_schema.json",
     "parameter": {
       "flight_height": 10,
       "decision_height": 2
     },
     "action": "mov_multiple",
     "commands": [
       { "action": "takeoff", "commands": { "time": 5 } },
       {
         "action": "mov_local",
         "commands": { "x": 48.766, "y": 11.423 }
       },
       {
         "action": "scan_area",
         "commands": {
           "polygon": [
             [48.766, 11.423], [48.767, 11.424], [48.768, 11.422]
           ],
           "height": 8,
           "overlap_ratio": 0.6
         }
       },
       { "action": "land_at", "commands": { "lat": 48.766, "lon": 11.423 } }
     ]
   }
