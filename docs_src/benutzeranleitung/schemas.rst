.. _schemas:

Schema
======

In diesem Abschnitt werden die json Schema dokumentiert, die im Payload
Computer Drone Projekt verwendet werden. Diese Schema definieren die Struktur
und Validierung der Daten, die zwischen den verschiedenen Komponenten des
Systems ausgetauscht werden.


Einleitung
----------

Hier finden Sie eine Übersicht und Beschreibung der relevanten Schema, die im Projekt verwendet werden. Details zu jedem Schema finden Sie in den jeweiligen Unterabschnitten.


Config-Schema
----------------
Das Config-Schema definiert die Struktur der Konfigurationsdateien, die für die Initialisierung und Anpassung des Systems verwendet werden. Es legt fest, welche Parameter erforderlich sind und welche optional sein können.
Die Datei config-schema.json dient als Schema zur Validierung von Konfigurationsdateien in JSON-Format. Sie definiert die zulässigen Schlüssel, Datentypen und mögliche Werte, um eine konsistente und fehlerfreie Konfiguration sicherzustellen
und zu ermöglichen, dass das System korrekt funktioniert. Dieses Schema ist entscheidend für die korrekte Initialisierung und Anpassung des Systems an spezifische Anforderungen und Umgebungen.
Das Schema stellt sicher, dass alle erforderlichen Parameter vorhanden sind und die richtigen Datentypen verwendet werden. Es hilft auch, mögliche Fehler in der Konfiguration frühzeitig zu erkennen und zu beheben, bevor sie zu Problemen im Betrieb führen können.


Die Datei config-schema.json ist im Verzeichnis `src/payload_computer/schemas/` zu finden.
Mission-Schema
----------------
Dieses Dokument beschreibt die Missionskonfiguration für Team Blau's Drohnenprojekt anhand des JSON-Schemas. Das Schema ermöglicht eine strukturierte Definition von Parametern, Aktionen und Befehlen für die Drohne.
Das JSON-Schema besteht aus mehreren Hauptelementen:
- Parameter: Definiert die Flugbedingungen (z. B. Flughöhe).
- Aktionen: Gibt den Typ der Mission an (z. B. "list" oder "mov_multiple").
- Befehle: Enthält spezifische Bewegungs- und Steuerungskommandos
- Bewegungsbefehle: Definiert die Bewegungsrichtung und Geschwindigkeit der Drohne.
- Steuerbefehle: Enthält Befehle zur Steuerung der Drohne, wie Start, Stopp und Notlandung.
Die Datei mission-schema.json ist im Verzeichnis `src/payload_computer/schemas/` zu finden.