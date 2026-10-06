import xml.etree.ElementTree as ET
import sys
import os
import random

if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.path.append('/usr/share/sumo/tools')

import sumolib

# 1. Parse peak buses
bus_file = 'mobility/guimaraes/buses.rou.xml'
tree = ET.parse(bus_file)
root = tree.getroot()

events = [] # (time, +1/-1)
for vehicle in root.findall('vehicle'):
    depart = float(vehicle.get('depart', 0))
    stops = vehicle.findall('.//stop')
    if stops:
        end_time = float(stops[-1].get('until', depart + 1800))
    else:
        end_time = depart + 1800
    events.append((depart, 1))
    events.append((end_time, -1))

events.sort()
current_buses = 0
max_buses = 0
for time, change in events:
    current_buses += change
    if current_buses > max_buses:
        max_buses = current_buses

print(f"Max simultaneous buses: {max_buses}")

# 2. Demands
TARGET_VCPUS = 130.0
bus_vcpus = max_buses * 2.0
missing_vcpus = TARGET_VCPUS - bus_vcpus
print(f"Baseline vCPU from buses: {bus_vcpus}")
print(f"Missing vCPUs to saturate (Target 130): {missing_vcpus}")

# 80% of missing vCPU for cars, 20% for bikes
car_vcpus = missing_vcpus * 0.8
bike_vcpus = missing_vcpus * 0.2

num_cars = int(car_vcpus / 0.5)
num_bikes = int(bike_vcpus / 0.1)

print(f"Generating {num_cars} cars and {num_bikes} bicycles.")

# 3. Localized Generation near MEC_1
net = sumolib.net.readNet('mobility/guimaraes/guimaraes.net.xml')
MEC_1_X = 4093.45
MEC_1_Y = 3992.89
RADIUS = 1500.0 # 1.5km to have enough connected edges

local_edges_passenger = []
local_edges_bicycle = []
for edge in net.getEdges():
    if edge.getFunction() == "internal":
        continue
    x1, y1 = edge.getFromNode().getCoord()
    x2, y2 = edge.getToNode().getCoord()
    dist1 = ((x1 - MEC_1_X)**2 + (y1 - MEC_1_Y)**2)**0.5
    dist2 = ((x2 - MEC_1_X)**2 + (y2 - MEC_1_Y)**2)**0.5
    if dist1 <= RADIUS or dist2 <= RADIUS:
        if edge.allows("passenger"):
            local_edges_passenger.append(edge)
        if edge.allows("bicycle"):
            local_edges_bicycle.append(edge)

print(f"Found {len(local_edges_passenger)} passenger edges and {len(local_edges_bicycle)} bicycle edges near MEC_1.")

# Write trips
with open('mobility/guimaraes/synth_cars.trip.xml', 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<routes>\n')
    for i in range(num_cars):
        edge1 = random.choice(local_edges_passenger)
        edge2 = random.choice(local_edges_passenger)
        while edge1 == edge2:
            edge2 = random.choice(local_edges_passenger)
        depart = 25200 + random.uniform(0, 5) # spawn within 5s
        f.write(f'    <trip id="synth_car_{i}" type="cars_passenger" depart="{depart:.1f}" from="{edge1.getID()}" to="{edge2.getID()}"/>\n')
    f.write('</routes>\n')

with open('mobility/guimaraes/synth_bikes.trip.xml', 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<routes>\n')
    for i in range(num_bikes):
        edge1 = random.choice(local_edges_bicycle)
        edge2 = random.choice(local_edges_bicycle)
        while edge1 == edge2:
            edge2 = random.choice(local_edges_bicycle)
        depart = 25200 + random.uniform(0, 5)
        f.write(f'    <trip id="synth_bike_{i}" type="bikes_bicycle" depart="{depart:.1f}" from="{edge1.getID()}" to="{edge2.getID()}"/>\n')
    f.write('</routes>\n')

