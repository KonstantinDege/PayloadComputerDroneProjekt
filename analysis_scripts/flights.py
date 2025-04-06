import os
from pyulog import ULog

# Ordnerpfad mit den Logdateien
path = r"C:\PyUlog\Blaue_Gruppe_Blauer_Copter"

# Dictionary zur Zählung der Takeoffs pro Nutzer
data = dict()

# Durchlaufe alle Dateien im angegebenen Ordner
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            file_path = os.path.join(root, file)
            # nimmt das erste Wort als Benutzerkennung
            user = file.split("_")[0]

            ulog = ULog(file_path)

            # Zähle alle Takeoff-Meldungen in der Datei
            takeoffs = sum(1 for entry in ulog.logged_messages
                           if "Takeoff detected" in entry.message)
            if takeoffs > 0:
                data[user] = data.get(user, 0) + takeoffs

# Ausgabe
print("Anzahl der Takeoffs pro Nutzer:")
for user, count in data.items():
    print(f"  {user}: {count}")
