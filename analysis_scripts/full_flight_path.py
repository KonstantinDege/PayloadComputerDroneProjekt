import os
import numpy as np
from pyulog import ULog

path = r"C:\Users\User\Desktop\05_FlightTests\Blaue_Gruppe_Blauer_Copter"

def get_dist(x,y,z):
    dist = 0
    for i in range(len(x)):
        if i == 0:
            continue
        else:
            dist += np.sqrt((x[i] - x[i-1])**2 + (y[i] - y[i-1])**2 + (z[i] - z[i-1])**2)
    return dist
    
    



data = dict()
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".ulg"):
            fi = os.path.join(root, file)

            ulog = ULog(fi)
            
            vehicle_local_position = next(x for x in ulog.data_list if x.name == "vehicle_local_position")



            full_flight_path = get_dist(vehicle_local_position.data["x"], vehicle_local_position.data["y"], vehicle_local_position.data["z"])

            if file[0:2] in data:
                data[file[0:2]].append(full_flight_path)
            else:
                data[file[0:2]] = [full_flight_path]

flight_distance_user = dict()

for (key, value) in data.items():
    for distance in value:
        flight_distance_user[key] = flight_distance_user.get(key, 0) + distance

print(f"Flight distance: {flight_distance_user}") # [m]

