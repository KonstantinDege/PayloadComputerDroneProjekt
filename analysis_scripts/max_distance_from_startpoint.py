import os
import numpy as np
from pyulog import ULog

# Pfad zum Ordner mit den Logdateien
path = r"C:\PyUlog\Blaue_Gruppe_Blauer_Copter"

# Dictionary zur Speicherung der Maximalentfernungen pro Nutzer
data = dict()

# Durchlaufe alle Log-Dateien im Ordner
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            file_path = os.path.join(root, file)
            user = file.split("_")[0]  # Erster Teil des Dateinamens = Nutzer

            ulog = ULog(file_path)

            try:
                vehicle_local_pos = ulog.get_dataset("vehicle_local_position")
                x, y, z = (
                    vehicle_local_pos.data["x"],
                    vehicle_local_pos.data["y"],
                    vehicle_local_pos.data["z"]
                    )
                distances = np.sqrt(x**2 + y**2 + z**2)
                max_dist = distances.max()
                data.setdefault(user, []).append(max_dist)
            except StopIteration:
                print(f"Keine Positionsdaten in Datei: {file}")

# Größte Entfernung vom Startpunkt je Nutzer
max_distance = {user: max(dist_list) for user, dist_list in data.items()}

# Ausgabe
print("Einzelne Maximalwerte je Flug [m]:")
for user, dists in data.items():
    formatted = [f"{d:.2f}" for d in dists]
    print(f"  {user}: {formatted}")

print("\nMaximaler Abstand vom Startpunkt pro Nutzer [m]:")
for user, dist in max_distance.items():
    print(f"  {user}: {dist:.2f}")
