import xml.etree.ElementTree as ET
import math
import matplotlib.pyplot as plt
import os

fcd_file = 'mobility/guimaraes/fcd_saturated_1h.xml'

mecs = {
    'MEC_0': (464.65, 8739.37),
    'MEC_1': (4093.45, 3992.89),
    'MEC_2': (5321.21, 7222.38)
}
mec_names = {
    'MEC_0': 'MEC_0 (Azurém)',
    'MEC_1': 'MEC_1 (Centro Histórico)',
    'MEC_2': 'MEC_2 (Veiga de Creixomil)'
}

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
counts = {m: {'bus': [], 'car': [], 'bike': []} for m in mecs}
loads = {m: [] for m in mecs}

current_time = 0.0
context = ET.iterparse(fcd_file, events=('start', 'end'))

for event, elem in context:
    if event == 'start' and elem.tag == 'timestep':
        current_time = float(elem.get('time')) - 25200.0
        cur_counts = {m: {'bus': 0, 'car': 0, 'bike': 0} for m in mecs}
        cur_loads = {m: 0.0 for m in mecs}
    elif event == 'start' and elem.tag == 'vehicle':
        vtype = elem.get('type', '').lower()
        x = float(elem.get('x'))
        y = float(elem.get('y'))
        
        if 'bus' in vtype: cat = 'bus'
        elif 'car' in vtype: cat = 'car'
        elif 'bike' in vtype or 'bicycle' in vtype: cat = 'bike'
        else: cat = 'car'
            
        closest_mec = get_closest_mec(x, y)
        load = profiles.get(cat, 0.5)
        
        cur_counts[closest_mec][cat] += 1
        cur_loads[closest_mec] += load
        
    elif event == 'end' and elem.tag == 'timestep':
        if int(current_time) % 10 == 0:
            times.append(current_time / 60.0)
            for m in mecs:
                for cat in ['bus', 'car', 'bike']:
                    counts[m][cat].append(cur_counts[m][cat])
                loads[m].append(cur_loads[m])
        elem.clear()

fig, axes = plt.subplots(3, 2, figsize=(16, 14))

# Compute maximum load across all zones to set y-axis limit dynamically
max_load_overall = max(max(loads[m]) if loads[m] else 0 for m in mecs)
# We want to show at least up to 35 to see the threshold, or more if it exceeded.
y_lim = max(35, max_load_overall + 5)

for i, m in enumerate(['MEC_0', 'MEC_1', 'MEC_2']):
    ax_ue = axes[i, 0]
    ax_ue.plot(times, counts[m]['bus'], label='Bus', color='blue', linewidth=2)
    ax_ue.plot(times, counts[m]['car'], label='Car', color='red', linewidth=2)
    ax_ue.plot(times, counts[m]['bike'], label='Bike', color='green', linewidth=2)
    ax_ue.set_xlabel('Tempo (Minutos)')
    ax_ue.set_ylabel('Nº Veículos')
    ax_ue.set_title(f'Contagem de UEs por Classe (Saturado) - {mec_names[m]}')
    ax_ue.legend()
    ax_ue.grid(True, linestyle='--', alpha=0.7)
    
    ax_load = axes[i, 1]
    ax_load.plot(times, loads[m], label=f'Carga Estimada {m}', color='purple', linewidth=2)
    ax_load.axhline(y=32.0, color='red', linestyle='--', label='Capacidade (32 vCPUs)')
    ax_load.set_xlabel('Tempo (Minutos)')
    ax_load.set_ylabel('vCPUs')
    ax_load.set_title(f'Carga Computacional (Saturado) - {mec_names[m]}')
    ax_load.set_ylim(0, y_lim) 
    
    # Shade the area where load exceeds 32 vCPUs
    ax_load.fill_between(times, 32.0, loads[m], where=[l > 32.0 for l in loads[m]], 
                         color='red', alpha=0.3, interpolate=True)
                         
    ax_load.legend()
    ax_load.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
output_png = 'mobility/guimaraes/detailed_analysis_saturated_1h.png'
plt.savefig(output_png, dpi=150)
print(f"Detailed plot saved to {output_png}")

total_loads = {k: sum(loads[k]) / len(loads[k]) for k in loads}
max_loads = {k: max(loads[k]) for k in loads}
print(f"Average Load MEC_0: {total_loads['MEC_0']:.1f}, Max: {max_loads['MEC_0']:.1f}")
print(f"Average Load MEC_1: {total_loads['MEC_1']:.1f}, Max: {max_loads['MEC_1']:.1f}")
print(f"Average Load MEC_2: {total_loads['MEC_2']:.1f}, Max: {max_loads['MEC_2']:.1f}")

