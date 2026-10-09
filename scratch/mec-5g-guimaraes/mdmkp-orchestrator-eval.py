import pulp
import random
import sys

# ==========================================
# 1. DEFINE HETEROGENEOUS PROFILES & MECS
# ==========================================
PROFILES = {
    "bus":   {"bw": 2.5,   "vcpu": 2.0, "ram": 4.0, "l_max": 40.0},
    "car":   {"bw": 0.024, "vcpu": 0.5, "ram": 1.0, "l_max": 40.0},
    "bike":  {"bw": 0.001, "vcpu": 0.1, "ram": 0.2, "l_max": 40.0}
}

MECS = {
    "MEC_0": {"bw": 1000.0, "vcpu": 8.0, "ram": 16.0},
    "MEC_1": {"bw": 1000.0, "vcpu": 8.0, "ram": 16.0},
    "MEC_2": {"bw": 1000.0, "vcpu": 8.0, "ram": 16.0}
}

VEHICLE_COUNTS = {"bus": 6, "car": 20, "bike": 10}
random.seed(42) 

services = []
for v_type, count in VEHICLE_COUNTS.items():
    for i in range(count):
        delays = [random.uniform(1.0, 5.0), random.uniform(8.0, 15.0), random.uniform(15.0, 30.0)]
        random.shuffle(delays)
        services.append({
            "id": f"{v_type}_{i}",
            "type": v_type,
            "delays": {"MEC_0": delays[0], "MEC_1": delays[1], "MEC_2": delays[2]}
        })

# ==========================================
# 3. BUILD THE MDMKP OPTIMIZATION MODEL
# ==========================================
def solve_mdmkp(services, mecs, profiles, relax_to_continuous=False):
    prob_name = "MEC_Migration_Relaxed" if relax_to_continuous else "MEC_Migration_Exact"
    prob = pulp.LpProblem(prob_name, pulp.LpMaximize)

    var_type = pulp.LpContinuous if relax_to_continuous else pulp.LpBinary
    indices = [(s["id"], m) for s in services for m in mecs.keys()]

    if hasattr(prob, "add_variable_dicts"):
        x = prob.add_variable_dicts("placement", indices, lowBound=0, upBound=1, cat=var_type)
    else:
        x = pulp.LpVariable.dicts("placement", indices, lowBound=0, upBound=1, cat=var_type)

    objective = []
    for s in services:
        req = profiles[s["type"]]
        for m in mecs.keys():
            delay = s["delays"][m]
            utility = req["l_max"] - delay
            objective.append(utility * x[s["id"], m])
            if delay > req["l_max"]:
                prob += x[s["id"], m] == 0, f"Latency_Violation_{s['id']}_{m}"

    prob += pulp.lpSum(objective), "Total_Latency_Savings"

    for s in services:
        prob += pulp.lpSum(x[s["id"], m] for m in mecs.keys()) <= 1.0, f"Single_Placement_{s['id']}"

    for m in mecs.keys():
        prob += pulp.lpSum(profiles[s["type"]]["bw"] * x[s["id"], m] for s in services) <= mecs[m]["bw"], f"Cap_BW_{m}"
        prob += pulp.lpSum(profiles[s["type"]]["vcpu"] * x[s["id"], m] for s in services) <= mecs[m]["vcpu"], f"Cap_vCPU_{m}"
        prob += pulp.lpSum(profiles[s["type"]]["ram"] * x[s["id"], m] for s in services) <= mecs[m]["ram"], f"Cap_RAM_{m}"

    try:
        if hasattr(pulp, "PULP_CBC_CMD"):
            status_code = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        else:
            available_solvers = pulp.listSolvers(onlyAvailable=True)
            if not available_solvers:
                print("ERRO CRITICO: Nenhum solver matematico encontrado!")
                sys.exit(1)
            solver = pulp.getSolver(available_solvers[0], msg=False)
            status_code = prob.solve(solver)
    except Exception as e:
        print(f"Solver Error: {e}")
        sys.exit(1)
    
    total_utility = pulp.value(prob.objective)
    admitted = sum(1 for s in services for m in mecs.keys() if pulp.value(x[s["id"], m]) > 0.99)
    
    utilization = {m: {"bw": 0, "vcpu": 0, "ram": 0} for m in mecs.keys()}
    for s in services:
        for m in mecs.keys():
            val = pulp.value(x[s["id"], m])
            if val > 0.001:
                utilization[m]["bw"] += profiles[s["type"]]["bw"] * val
                utilization[m]["vcpu"] += profiles[s["type"]]["vcpu"] * val
                utilization[m]["ram"] += profiles[s["type"]]["ram"] * val

    # Cross-version status extraction
    if hasattr(prob, "status") and hasattr(pulp, "LpStatus"):
        status_str = pulp.LpStatus[prob.status]
    else:
        status_enum = getattr(status_code, "status", "Solved")
        status_str = getattr(status_enum, "name", str(status_enum))

    return status_str, total_utility, admitted, utilization

status_exact, utility_exact, admitted_exact, util_exact = solve_mdmkp(services, MECS, PROFILES, relax_to_continuous=False)
status_relax, utility_relax, admitted_relax, util_relax = solve_mdmkp(services, MECS, PROFILES, relax_to_continuous=True)

print("--- MDMKP Analytical Evaluation ---")
print(f"Total Vehicles: {len(services)} (6 Buses, 20 Cars, 10 Bikes)\n")

print("[1] ILP Exact Solution (Realistic Assignment)")
print(f"Status: {status_exact}")
print(f"Total Latency Savings: {utility_exact:.2f} ms")
print(f"Services Admitted to Edge: {admitted_exact} / {len(services)}")
for m, usage in util_exact.items():
    print(f"  - {m} Load: vCPU {usage['vcpu']:5.1f}/{MECS[m]['vcpu']} | RAM {usage['ram']:5.1f}/{MECS[m]['ram']} | BW {usage['bw']:5.1f}/{MECS[m]['bw']}")

print("\n[2] LP Fractional Relaxation (Theoretical Upper Bound)")
print(f"Status: {status_relax}")
print(f"Total Latency Savings: {utility_relax:.2f} ms")
print(f"Efficiency Gap (Exact vs Bound): {(utility_exact / utility_relax) * 100:.2f}%")
