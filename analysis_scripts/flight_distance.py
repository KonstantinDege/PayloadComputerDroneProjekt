import os
import numpy as np
from pyulog import ULog

# Pfad zum Ordner mit den Log-Dateien
path = r"C:\PyUlog\Blaue_Gruppe_Blauer_Copter"


# Funktion zur Berechnung der Flugdistanz
def get_dist(x, y, z):
    dist = 0
    for i in range(1, len(x)):
        dx = x[i] - x[i - 1]
        dy = y[i] - y[i - 1]
        dz = z[i] - z[i - 1]
        dist += np.sqrt(dx**2 + dy**2 + dz**2)
    return dist


# Flugstrecken sammeln
data = dict()

for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            file_path = os.path.join(root, file)
            # nimmt das erste Wort als Benutzerkennung
            user = file.split("_")[0]

            ulog = ULog(file_path)

            # Positionsdaten
            try:
                vehicle_local_pos = ulog.get_dataset("vehicle_local_position")
                full_flight_path = get_dist(
                    vehicle_local_pos.data["x"],
                    vehicle_local_pos.data["y"],
                    vehicle_local_pos.data["z"]
                    )
                data.setdefault(user, []).append(full_flight_path)
            except StopIteration:
                print(f"Keine Positionsdaten in Datei: {file}")

# Gesamtdistanz pro Nutzer
flight_distance_user = {user: sum(dist_list)
                        for user, dist_list in data.items()}

# Ausgabe
print("Geflogene Distanzen pro Nutzer [m]:")
for user, dist_list in data.items():
    dist_formatted = [f"{d:.2f}" for d in dist_list]
    print(f"  {user}: {dist_formatted}")

print("\nGesamtdistanz pro Nutzer [m]:")
for user, total in flight_distance_user.items():
    print(f"  {user}: {total:.2f}")
