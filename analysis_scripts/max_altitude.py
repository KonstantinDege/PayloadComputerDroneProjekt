import os
import numpy as np
from pyulog import ULog

# You need to set the path to the directory containing the flight logs.
path = r"C:\Users\User\Desktop\05_FlightTests\Blaue_Gruppe_Blauer_Copter"

# This script calculates the maximum altitude of each flight log in a given directory.
# It assumes that the flight logs are in ULog format and contain a message named "vehicle_local_position".
data = dict()
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            fi = os.path.join(root, file)

            ulog = ULog(fi)
            
            vehicle_local_position = next(x for x in ulog.data_list if x.name == "vehicle_local_position")
            
            max_altitude = abs(vehicle_local_position.data["z"])

            if file[0:2] in data:
                data[file[0:2]].append(max_altitude.max())
            else:
                data[file[0:2]] = [max_altitude.max()]


max_height = dict()

for (key, value) in data.items():
    for max_altitude in value:
        if max_altitude > max_height.get(key, 0):
            max_height[key] = max_altitude

print(f"Max height: {max_height}") # [m]