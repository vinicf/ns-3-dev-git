import xml.etree.ElementTree as ET
import math
import matplotlib.pyplot as plt
import os

fcd_file = 'mobility/guimaraes/fcd_1h.xml'

# MEC Coordinates
mecs = {
    'MEC_0': (464.65, 8739.37),
    'MEC_1': (4093.45, 3992.89),
    'MEC_2': (5321.21, 7222.38)
}

# Resource Profiles
profiles = {
    'bus': 2.0,
    'car': 0.5,
    'bike': 0.1,
    'bicycle': 0.1
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

times = []
counts = {'bus': [], 'car': [], 'bike': []}
loads = {'MEC_0': [], 'MEC_1': [], 'MEC_2': []}

current_time = 0.0
current_counts = {'bus': 0, 'car': 0, 'bike': 0}
current_loads = {'MEC_0': 0.0, 'MEC_1': 0.0, 'MEC_2': 0.0}

context = ET.iterparse(fcd_file, events=('start', 'end'))

for event, elem in context:
    if event == 'start' and elem.tag == 'timestep':
        current_time = float(elem.get('time')) - 25200.0
        current_counts = {'bus': 0, 'car': 0, 'bike': 0}
        current_loads = {'MEC_0': 0.0, 'MEC_1': 0.0, 'MEC_2': 0.0}
    elif event == 'start' and elem.tag == 'vehicle':
        vtype = elem.get('type', '').lower()
        x = float(elem.get('x'))
        y = float(elem.get('y'))
        
        # Classify
        if 'bus' in vtype:
            cat = 'bus'
        elif 'car' in vtype:
            cat = 'car'
        elif 'bike' in vtype or 'bicycle' in vtype:
            cat = 'bike'
        else:
            cat = 'car' # default
            
        current_counts[cat] += 1
        
        # Load
        load = profiles.get(cat, 0.5)
        closest_mec = get_closest_mec(x, y)
        current_loads[closest_mec] += load
        
    elif event == 'end' and elem.tag == 'timestep':
        # Every 10 seconds to reduce plot density, or every second
        if int(current_time) % 10 == 0:
            times.append(current_time / 60.0) # convert to minutes for x-axis
            for k in counts: counts[k].append(current_counts[k])
            for k in loads: loads[k].append(current_loads[k])
        elem.clear()

plt.figure(figsize=(14, 6))

# Plot 1: UEs
plt.subplot(1, 2, 1)
plt.plot(times, counts['bus'], label='Bus', color='blue', linewidth=2)
plt.plot(times, counts['car'], label='Car', color='red', linewidth=2)
plt.plot(times, counts['bike'], label='Bike', color='green', linewidth=2)
plt.xlabel('Tempo de Simulação (Minutos)')
plt.ylabel('Número de Veículos Ativos')
plt.title('Contagem de UEs por Classe (1 Hora)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)

# Plot 2: Loads
plt.subplot(1, 2, 2)
plt.plot(times, loads['MEC_0'], label='MEC_0 (Azurém)', color='purple', linewidth=2)
plt.plot(times, loads['MEC_1'], label='MEC_1 (Centro Histórico)', color='orange', linewidth=2)
plt.plot(times, loads['MEC_2'], label='MEC_2 (Veiga de Creixomil)', color='brown', linewidth=2)
plt.axhline(y=32.0, color='red', linestyle='--', label='Capacidade Max por MEC (32 vCPUs)')
plt.xlabel('Tempo de Simulação (Minutos)')
plt.ylabel('Carga Computacional Estimada (vCPUs)')
plt.title('Carga por Zona MEC (1 Hora)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
output_png = 'mobility/guimaraes/base_scenario_analysis_1h.png'
plt.savefig(output_png, dpi=150)
print(f"Plot saved to {output_png}")

# Generate text summary for the markdown
total_loads = {k: sum(loads[k]) / len(loads[k]) for k in loads}
max_loads = {k: max(loads[k]) for k in loads}
print(f"Average Load MEC_0: {total_loads['MEC_0']:.1f}, Max: {max_loads['MEC_0']:.1f}")
print(f"Average Load MEC_1: {total_loads['MEC_1']:.1f}, Max: {max_loads['MEC_1']:.1f}")
print(f"Average Load MEC_2: {total_loads['MEC_2']:.1f}, Max: {max_loads['MEC_2']:.1f}")

