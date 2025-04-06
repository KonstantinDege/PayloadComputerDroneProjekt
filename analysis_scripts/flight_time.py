import os
from pyulog import ULog

# Pfad zum Ordner mit den .ulg-Dateien
path = r"C:\PyUlog\Blaue_Gruppe_Blauer_Copter"

# Dictionaries zur Speicherung der Flugzeiten
data = dict()
longest_per_flight = dict()
time_per_user = dict()

# Datei für Protokollnachrichten (Start & Landung)
with open("takeoff_messages.txt", "w") as f:
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".ulg"):
                file_path = os.path.join(root, file)
                # nimmt das erste Wort als Benutzerkennung
                user = file.split("_")[0]

                ulog = ULog(file_path)

                last_start = None
                for entry in ulog.logged_messages:
                    if "Takeoff detected" in entry.message:
                        last_start = entry.timestamp
                        f.write(f"{entry.timestamp}: {entry.message}\n")

                    if "Landing detected" in entry.message and last_start:
                        # in Minuts
                        flight_duration = (entry.timestamp - last_start
                                           ) / 1e6 / 60
                        f.write(f"{entry.timestamp}: {entry.message}\n")

                        data.setdefault(user, []).append(flight_duration)
                        # Zurücksetzen für den nächsten Start
                        last_start = None

# Längste Flugzeit pro Nutzer berechnen
for user, flights in data.items():
    longest_per_flight[user] = max(flights)
    time_per_user[user] = sum(flights)

# Ausgabe
print("Alle Flugzeiten pro Nutzer [min]:")
for user, flights in data.items():
    print(f"  {user}: {['{:.2f}'.format(f) for f in flights]}")

print("\nLängste Flugzeit pro Nutzer [min]:")
for user, longest in longest_per_flight.items():
    print(f"  {user}: {longest:.2f}")

print("\nGesamtflugzeit pro Nutzer [min]:")
for user, total in time_per_user.items():
    print(f"  {user}: {total:.2f}")
