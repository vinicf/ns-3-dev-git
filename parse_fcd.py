import xml.etree.ElementTree as ET

fcd_file = 'mobility/guimaraes/fcd_base.xml'

tree = ET.parse(fcd_file)
root = tree.getroot()

max_total = 0
max_breakdown = {}

for timestep in root.findall('timestep'):
    time = float(timestep.get('time'))
    vehicles = timestep.findall('vehicle')
    total = len(vehicles)
    
    if total > max_total:
        max_total = total
        counts = {'bus': 0, 'car': 0, 'bike': 0, 'other': 0}
        for v in vehicles:
            vtype = v.get('type', '')
            if 'bus' in vtype:
                counts['bus'] += 1
            elif 'car' in vtype:
                counts['car'] += 1
            elif 'bike' in vtype or 'bicycle' in vtype:
                counts['bike'] += 1
            else:
                counts['other'] += 1
        max_breakdown = counts

print(f"Max Total: {max_total}")
print(f"Breakdown at peak: {max_breakdown}")
