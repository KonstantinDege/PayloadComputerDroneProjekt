import os
from pyulog import ULog

# Pfad zum Ordner mit den Logdateien
path = r"C:\PyUlog\Blaue_Gruppe_Blauer_Copter"

# Dictionary zur Speicherung aller Entladeströme pro Nutzer
data = dict()

# Durchlaufe alle Log-Dateien im Ordner
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            file_path = os.path.join(root, file)
            # nimmt das erste Wort als Benutzerkennung
            user = file.split("_")[0]

            ulog = ULog(file_path)

            try:
                battery_status = ulog.get_dataset("battery_status")
                max_current = battery_status.data["current_a"].max()
                data.setdefault(user, []).append(max_current)
            except StopIteration:
                print(f"Keine Batteriedaten in Datei: {file}")

# Höchster Entladestrom pro Nutzer berechnen
max_discharge_current = {user: max(currents)
                         for user, currents in data.items()}

# Ausgabe
print("Maximaler Entladestrom je Flug [A]:")
for user, currents in data.items():
    formatted = [f"{c:.2f}" for c in currents]
    print(f"  {user}: {formatted}")

print("\nMaximaler Entladestrom pro Nutzer [A]:")
for user, current in max_discharge_current.items():
    print(f"  {user}: {current:.2f}")
