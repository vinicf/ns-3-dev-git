import pulp
import random
import math

# ==========================================
# 1. DEFINE HETEROGENEOUS PROFILES & MECS
# ==========================================

# Application Profiles based on your ns-3 UDP implementations
# Demands: [BW (Mbps), vCPU (Cores), RAM (GB)], Max Latency (ms)
PROFILES = {
    "bus":   {"bw": 2.5,   "vcpu": 2.0, "ram": 4.0, "l_max": 40.0},  # Heavy video/CBR
    "car":   {"bw": 0.024, "vcpu": 0.5, "ram": 1.0, "l_max": 20.0},  # 300B @ 10Hz CAMs
    "bike":  {"bw": 0.001, "vcpu": 0.1, "ram": 0.2, "l_max": 100.0}  # 100B @ 1Hz beacons
}

# MEC Capacities: [BW (Mbps), vCPU (Cores), RAM (GB)]
# Modeled for 3 Hub gNBs
MECS = {
    "MEC_0": {"bw": 100.0, "vcpu": 32.0, "ram": 64.0},
    "MEC_1": {"bw": 100.0, "vcpu": 32.0, "ram": 64.0},
    "MEC_2": {"bw": 100.0, "vcpu": 32.0, "ram": 64.0}
}

# ==========================================
# 2. GENERATE SYNTHETIC VEHICULAR TRAFFIC
# ==========================================
NUM_VEHICLES = 80
random.seed(42) # For reproducible results

services = []
for i in range(NUM_VEHICLES):
    # Randomly assign a vehicle type
    v_type = random.choices(["bus", "car", "bike"], weights=[0.1, 0.7, 0.2])[0]
    
    # Generate random delays to each MEC (simulating spatial distribution)
    # E.g., one local MEC (~2ms), one neighbor (~10ms), one far (~20ms)
    delays = [random.uniform(1.0, 5.0), random.uniform(8.0, 15.0), random.uniform(15.0, 30.0)]
    random.shuffle(delays)
    
    services.append({
        "id": f"ue_{i}",
        "type": v_type,
        "delays": {"MEC_0": delays[0], "MEC_1": delays[1], "MEC_2": delays[2]}
    })

# ==========================================
# 3. BUILD THE MDMKP OPTIMIZATION MODEL
# ==========================================
def solve_mdmkp(services, mecs, profiles, relax_to_continuous=False):
    # Initialize the LP Maximization Problem
    prob_name = "MEC_Migration_Relaxed" if relax_to_continuous else "MEC_Migration_Exact"
    prob = pulp.LpProblem(prob_name, pulp.LpMaximize)

    # Decision Variables: x[i][j] = 1 if service i is placed on MEC j
    # If relaxed, variables can take fractional values between 0 and 1
    var_type = pulp.LpContinuous if relax_to_continuous else pulp.LpBinary
    x = pulp.LpVariable.dicts("placement", 
                              ((s["id"], m) for s in services for m in mecs.keys()), 
                              lowBound=0, upBound=1, cat=var_type)

    # Objective Function: Maximize Total Latency Savings (L_max - delay)
    objective = []
    for s in services:
        req = profiles[s["type"]]
        for m in mecs.keys():
            delay = s["delays"][m]
            # Utility = Latency savings. If delay > L_max, utility is negative.
            utility = req["l_max"] - delay
            objective.append(utility * x[s["id"], m])
            
            # Constraint: Force variable to 0 if latency threshold is violated
            if delay > req["l_max"]:
                prob += x[s["id"], m] == 0, f"Latency_Violation_{s['id']}_{m}"

    prob += pulp.lpSum(objective), "Total_Latency_Savings"

    # Constraint 1: Single Choice (A service is placed on AT MOST 1 MEC)
    # (Using <= 1 means if no MEC can host it, it drops to the Cloud)
    for s in services:
        prob += pulp.lpSum(x[s["id"], m] for m in mecs.keys()) <= 1.0, f"Single_Placement_{s['id']}"

    # Constraint 2: Multi-Dimensional Capacity Bounds for each MEC
    for m in mecs.keys():
        prob += pulp.lpSum(profiles[s["type"]]["bw"] * x[s["id"], m] for s in services) <= mecs[m]["bw"], f"Cap_BW_{m}"
        prob += pulp.lpSum(profiles[s["type"]]["vcpu"] * x[s["id"], m] for s in services) <= mecs[m]["vcpu"], f"Cap_vCPU_{m}"
        prob += pulp.lpSum(profiles[s["type"]]["ram"] * x[s["id"], m] for s in services) <= mecs[m]["ram"], f"Cap_RAM_{m}"

    # ==========================================
    # 4. SOLVE AND EXTRACT RESULTS
    # ==========================================
    # Suppress verbose solver output
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    total_utility = pulp.value(prob.objective)
    admitted = sum(1 for s in services for m in mecs.keys() if pulp.value(x[s["id"], m]) > 0.99)
    
    # Calculate resource utilization
    utilization = {m: {"bw": 0, "vcpu": 0, "ram": 0} for m in mecs.keys()}
    for s in services:
        for m in mecs.keys():
            val = pulp.value(x[s["id"], m])
            if val > 0.001:  # Account for fractional assignments in relaxation
                utilization[m]["bw"] += profiles[s["type"]]["bw"] * val
                utilization[m]["vcpu"] += profiles[s["type"]]["vcpu"] * val
                utilization[m]["ram"] += profiles[s["type"]]["ram"] * val

    return prob.status, total_utility, admitted, utilization

# Run Exact ILP
status_exact, utility_exact, admitted_exact, util_exact = solve_mdmkp(services, MECS, PROFILES, relax_to_continuous=False)

# Run Fractional Relaxation (Theoretical Upper Bound)
status_relax, utility_relax, admitted_relax, util_relax = solve_mdmkp(services, MECS, PROFILES, relax_to_continuous=True)

# Print Summary
print("--- MDMKP Analytical Evaluation ---")
print(f"Total Vehicles: {NUM_VEHICLES}\n")

print("[1] ILP Exact Solution (Realistic Assignment)")
print(f"Status: {pulp.LpStatus[status_exact]}")
print(f"Total Latency Savings: {utility_exact:.2f} ms")
print(f"Services Admitted to Edge: {admitted_exact} / {NUM_VEHICLES}")
for m, usage in util_exact.items():
    print(f"  - {m} Load: vCPU {usage['vcpu']:5.1f}/{MECS[m]['vcpu']} | RAM {usage['ram']:5.1f}/{MECS[m]['ram']} | BW {usage['bw']:5.1f}/{MECS[m]['bw']}")

print("\n[2] LP Fractional Relaxation (Theoretical Upper Bound)")
print(f"Status: {pulp.LpStatus[status_relax]}")
print(f"Total Latency Savings: {utility_relax:.2f} ms")
print(f"Efficiency Gap (Exact vs Bound): {(utility_exact / utility_relax) * 100:.2f}%")