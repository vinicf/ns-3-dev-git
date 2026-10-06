import xml.etree.ElementTree as ET
import math
import matplotlib.pyplot as plt
import os

fcd_file = 'mobility/guimaraes/fcd_60s.xml'
tree = ET.parse(fcd_file)
root = tree.getroot()

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

for timestep in root.findall('timestep'):
    t = float(timestep.get('time')) - 25200.0 # normalize to 0-60
    times.append(t)
    
    current_counts = {'bus': 0, 'car': 0, 'bike': 0}
    current_loads = {'MEC_0': 0.0, 'MEC_1': 0.0, 'MEC_2': 0.0}
    
    for v in timestep.findall('vehicle'):
        vtype = v.get('type', '').lower()
        x = float(v.get('x'))
        y = float(v.get('y'))
        
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
        
    for k in counts: counts[k].append(current_counts[k])
    for k in loads: loads[k].append(current_loads[k])

plt.figure(figsize=(14, 6))

# Plot 1: UEs
plt.subplot(1, 2, 1)
plt.plot(times, counts['bus'], label='Bus', color='blue', linewidth=2)
plt.plot(times, counts['car'], label='Car', color='red', linewidth=2)
plt.plot(times, counts['bike'], label='Bike', color='green', linewidth=2)
plt.xlabel('Tempo de Simulação (s)')
plt.ylabel('Número de Veículos Ativos')
plt.title('Contagem de UEs por Classe (0-60s)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)

# Plot 2: Loads
plt.subplot(1, 2, 2)
plt.plot(times, loads['MEC_0'], label='MEC_0 (Azurém)', color='purple', linewidth=2)
plt.plot(times, loads['MEC_1'], label='MEC_1 (Centro Histórico)', color='orange', linewidth=2)
plt.plot(times, loads['MEC_2'], label='MEC_2 (Veiga de Creixomil)', color='brown', linewidth=2)
plt.axhline(y=32.0, color='red', linestyle='--', label='Capacidade Max por MEC (32 vCPUs)')
plt.xlabel('Tempo de Simulação (s)')
plt.ylabel('Carga Computacional Estimada (vCPUs)')
plt.title('Carga por Zona MEC (0-60s)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
artifact_dir = '/home/vinicius/.gemini/antigravity/brain/b7bdc223-f7c6-4fc6-a3c6-67560eb7a5bc'
plt.savefig(os.path.join(artifact_dir, 'base_scenario_analysis.png'), dpi=150)
print(f"Plot saved to {os.path.join(artifact_dir, 'base_scenario_analysis.png')}")

# Generate text summary for the markdown
total_loads = {k: sum(loads[k]) / len(loads[k]) for k in loads}
print(f"Average Load MEC_0: {total_loads['MEC_0']:.1f}")
print(f"Average Load MEC_1: {total_loads['MEC_1']:.1f}")
print(f"Average Load MEC_2: {total_loads['MEC_2']:.1f}")

