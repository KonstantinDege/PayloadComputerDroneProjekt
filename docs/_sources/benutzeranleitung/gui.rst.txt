.. _gui:

GUI Benutzeranleitung
=====================

Einleitung
----------

In diesem Abschnitt wird die grafische Benutzeroberfläche (GUI) des Payload
Computer Drone Projekts beschrieben. Die Anleitung erklärt die wichtigsten
Funktionen und die Bedienung der Oberfläche.


Benutzerhandbuch
----------------

- USB-C-Anschluss von Stromverteilerplatine in Raspberry Pi einstecken, falls nicht bereits erfolgt.
- USB-B-Stick in Raspberry Pi einstecken.
- Akku anschließen.
- Die LED in der Mitte des Raspberry Pi muss dauerhaft grün leuchten. Das bedeutet, dass dieser mit Strom versorgt wird.
- Falls der Raspberry Pi keinen Strom bekommt und die LED dementsprechend rot leuchtet, kann man eine andere Stromquelle, zum Beispiel eine Powerbank, an den USB-C-Port anschließen und testen.
- Mit dem Netzwerk der jeweiligen Drohne verbinden oder beide Geräte in ein gemeinsames Netzwerk bringen.

GUI
---

Admin Panel – Schnellstartanleitung
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mit dem Raspberry Pi verbinden
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Geben Sie die Raspi-IP ein (z.B. ``ltraspi02.local:4269``).
- Klicken Sie auf den **CONNECT RASPI**-Button.

Datensatz hochladen
^^^^^^^^^^^^^^^^^^^
- Ziehen Sie Ihre Datensatzdatei in das Feld **Upload datasets**.
- Warten Sie, bis der Upload-Fortschritt 100 % erreicht.

Missionsdatei anzeigen/bearbeiten
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Der Inhalt der Missionsdatei wird im Textfeld angezeigt.
- Sie enthält JSON-formatierte Befehle, z.B.:
    - ``"start_camera"``
    - ``"delay"``
    - ``"takeoff"``
    - ``"land_at"``

Missionsdatei auswählen
^^^^^^^^^^^^^^^^^^^^^^^
- Wählen Sie eine Missionsdatei zum Senden aus (z.B. ``test_mission.json``).

Mission senden
^^^^^^^^^^^^^^
- Klicken Sie auf den **SEND MISSION**-Button, um die ausgewählte Missionsdatei an den Raspberry Pi zu senden.


Backup
------

Backup über Webinterface
~~~~~~~~~~~~~~~~~~~~~~~~

- Mit einem Internetbrowser ``<ip>:4269/docs`` (z.B.
  ``ltraspi02.local:4269/docs``) öffnen. ``<ip>`` steht für die IP-Adresse.

- Mission File hochladen und ausführen.

Weitere Abschnitte können hier ergänzt werden.
