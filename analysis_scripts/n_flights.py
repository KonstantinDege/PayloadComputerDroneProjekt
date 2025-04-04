from pyulog import ULog
import os

path = r"C:\Users\User\Desktop\05_FlightTests\Blaue_Gruppe_Blauer_Copter"


data = dict()

for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            f = os.path.join(root, file)

            ulog = ULog(f)
            for entry in ulog.logged_messages:
                if "Takeoff detected" in entry.message:
                    data[file[0:2]] = data.get(file[0:2], 0) + 1

print(f"Number of takeoff messages: {data}")