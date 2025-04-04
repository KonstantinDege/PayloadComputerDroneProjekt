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
            
            battery_status = next(x for x in ulog.data_list if x.name == "battery_status")
            current = battery_status.data["current_a"]
            discharge_current = current.max()

            if file[0:2] in data:
                data[file[0:2]].append(current.max())
            else:
                data[file[0:2]] = [current.max()]

max_discharge_current = dict()

for (key, value) in data.items():
    for i in value:
        if i > max_discharge_current.get(key, 0):
            max_discharge_current[key] = i
print(f"Max discharge current: {max_discharge_current}") # [A]