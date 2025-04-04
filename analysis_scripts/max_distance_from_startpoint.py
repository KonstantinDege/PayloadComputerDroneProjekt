import os
import numpy as np
from pyulog import ULog

path = r"C:\Users\User\Desktop\05_FlightTests\Blaue_Gruppe_Blauer_Copter"

data = dict()
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            fi = os.path.join(root, file)

            ulog = ULog(fi)
            
            vehicle_local_position = next(x for x in ulog.data_list if x.name == "vehicle_local_position")

            distance = np.sqrt(vehicle_local_position.data["x"]**2 + vehicle_local_position.data["y"]**2 + vehicle_local_position.data["z"]**2)

            if file[0:2] in data:
                data[file[0:2]].append(distance.max())
            else:
                data[file[0:2]] = [distance.max()]

max_distance = dict()

for (key, value) in data.items():
    for i in value:
        if i > max_distance.get(key, 0):
            max_distance[key] = i

print(f"Max height: {max_distance}") # [m]