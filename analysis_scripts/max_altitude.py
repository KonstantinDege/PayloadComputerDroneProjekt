import os
from pyulog import ULog

# Pfad zum Log-Ordner
path = r"C:\PyUlog\Blaue_Gruppe_Blauer_Copter"

# Dictionary zur Speicherung aller Maximalhöhen pro Nutzer
data = dict()

# Durchlaufe alle .ulg-Dateien im Ordner
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            file_path = os.path.join(root, file)
            # nimmt das erste Wort als Benutzerkennung
            user = file.split("_")[0]

            ulog = ULog(file_path)

            try:
                pos = ulog.get_dataset("vehicle_local_position")
                max_altitude = abs(pos.data["z"]).max()
                data.setdefault(user, []).append(max_altitude)
            except StopIteration:
                print(f"Keine Positionsdaten in Datei: {file}")

# Höchste Flughöhe je Nutzer berechnen
max_height = {user: max(altitudes) for user, altitudes in data.items()}

# Ausgabe
print("Maximalhöhen je Flug [m]:")
for user, altitudes in data.items():
    formatted = [f"{a:.2f}" for a in altitudes]
    print(f"  {user}: {formatted}")

print("\nHöchste erreichte Flughöhe pro Nutzer [m]:")
for user, max_alt in max_height.items():
    print(f"  {user}: {max_alt:.2f}")
