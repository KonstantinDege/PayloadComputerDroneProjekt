import os
from pyulog import ULog

path = r"C:\Users\User\Desktop\05_FlightTests\Blaue_Gruppe_Blauer_Copter"


data = dict()
longest = 0


with open("takeoff_messages.txt", "w") as f:
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".ulg"):
                fi = os.path.join(root, file)

                ulog = ULog(fi)
                for entry in ulog.logged_messages:
                    if "Takeoff detected" in entry.message:
                        last_start = entry.timestamp
                        f.write(f"{entry.timestamp}: {entry.message}\n")
                    if "Landing detected" in entry.message:
                        print((entry.timestamp - last_start) / 1e6 / 60)
                        f.write(f"{entry.timestamp}: {entry.message}\n")
                        d = (entry.timestamp - last_start) / 1e6 / 60
                        if file[0:2] in data:
                            data[file[0:2]].append(d)
                        else:
                            data[file[0:2]] = [d]


longest_per_flight = dict()

for (key, value) in data.items():
    for flight_time in value:
        if flight_time > longest_per_flight.get(key, 0):
            longest_per_flight[key] = flight_time

time_per_user = dict()

for (key, value) in data.items():
    for flight_time in value:
        time_per_user[key] = time_per_user.get(key, 0) + flight_time




print(f"Flight time: {data}") # [min]
print(f"Longest flight time: {longest_per_flight}") # [min]
print(f"Time per user: {time_per_user}") # [min]
