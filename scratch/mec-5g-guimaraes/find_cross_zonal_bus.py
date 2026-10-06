import xml.etree.ElementTree as ET
import math
import os
import subprocess

# 1. Create buses_only.sumocfg
with open('mobility/guimaraes/buses_only.sumocfg', 'w') as f:
    f.write('''<?xml version='1.0' encoding='utf-8'?>
<configuration>
    <input>
        <net-file value="guimaraes.net.xml" />
        <route-files value="buses.rou.xml" />
        <additional-files value="vtypes.xml,ptstops.xml,buses.add.xml" />
    </input>
    <time>
        <step-length value="1.0" />
    </time>
</configuration>
''')

# 2. Run SUMO to get FCD
print("Running SUMO for buses only to get accurate timings...")
subprocess.run(['sumo', '-c', 'mobility/guimaraes/buses_only.sumocfg', 
                '--fcd-output', 'mobility/guimaraes/fcd_buses.xml', 
                '--no-step-log', 'true'])

# 3. Parse FCD
mecs = {
    'MEC_0': (464.65, 8739.37),
    'MEC_1': (4093.45, 3992.89),
    'MEC_2': (5321.21, 7222.38)
}

def get_closest_mec(x, y):
    min_dist = float('inf')
    closest = None
    for mec, coord in mecs.items():
        dist = math.hypot(x - coord[0], y - coord[1])
        if dist < min_dist:
            min_dist = dist
            closest = mec
    return closest

bus_zones = {} # bus_id -> list of dicts: {'zone': zone, 'enter_time': t, 'leave_time': t}
bus_lines = {}

# Parse buses.rou.xml to get line mapping
buses_tree = ET.parse('mobility/guimaraes/buses.rou.xml')
for v in buses_tree.getroot().findall('vehicle'):
    bus_lines[v.get('id')] = v.get('line', 'Unknown')

context = ET.iterparse('mobility/guimaraes/fcd_buses.xml', events=('start', 'end'))
current_time = 0.0

print("Parsing FCD...")
for event, elem in context:
    if event == 'start' and elem.tag == 'timestep':
        current_time = float(elem.get('time'))
    elif event == 'end' and elem.tag == 'vehicle':
        vid = elem.get('id')
        x = float(elem.get('x'))
        y = float(elem.get('y'))
        
        zone = get_closest_mec(x, y)
        
        if vid not in bus_zones:
            bus_zones[vid] = [{'zone': zone, 'enter_time': current_time, 'leave_time': current_time}]
        else:
            last_entry = bus_zones[vid][-1]
            if last_entry['zone'] == zone:
                last_entry['leave_time'] = current_time
            else:
                bus_zones[vid].append({'zone': zone, 'enter_time': current_time, 'leave_time': current_time})
        elem.clear()

# Find buses that visit all three zones
print("\nResults:")
found = False
for vid, zones in bus_zones.items():
    unique_zones = set(z['zone'] for z in zones)
    if len(unique_zones) == 3:
        found = True
        line = bus_lines.get(vid, 'Unknown')
        print(f"\nBus: {vid} (Line: {line})")
        
        seq = " -> ".join([z['zone'] for z in zones])
        print(f"Sequence: {seq}")
        
        total_time = zones[-1]['leave_time'] - zones[0]['enter_time']
        print(f"Total time in simulation: {total_time:.1f} s ({total_time/60:.1f} mins)")
        
        # Calculate time between first zone entry and last zone entry
        visited_zones = set()
        first_zone_time = zones[0]['enter_time']
        last_zone_enter_time = 0
        for z in zones:
            visited_zones.add(z['zone'])
            if len(visited_zones) == 3:
                last_zone_enter_time = z['enter_time']
                break
        
        cross_time = last_zone_enter_time - first_zone_time
        print(f"Time to cross from 1st zone to 3rd zone: {cross_time:.1f} s ({cross_time/60:.1f} mins)")
        
        # Print timeline
        for z in zones:
            print(f"  - {z['zone']}: {z['enter_time']:.1f}s to {z['leave_time']:.1f}s")

if not found:
    print("Nenhum autocarro visita as três zonas.")

