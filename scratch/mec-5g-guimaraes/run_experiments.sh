#!/bin/bash

# ==============================================================================
# NS-3 Experiment Runner: MDMKP Orchestration vs Spatial Edge Routing (PARALLEL)
# ==============================================================================

# Common Parameters (Golden Ratio & Saturated Scenario)
SUMO_CONFIG="mobility/guimaraes/guimaraes_saturated.sumocfg"
GNB_POSITIONS="mobility/guimaraes/gnb_positions.json"
MEC_TOPOLOGY="mobility/guimaraes/mec_topology.json"
DURATION=300
MAX_UES=512
MAX_BUSES=6
MAX_CARS=20
MAX_BICYCLES=10
FAST_CHANNEL="true"

NUM_RUNS=5

# Determine Number of Concurrent Jobs
CORES=$(nproc 2>/dev/null || echo 4)
# Limits the maximum concurrent jobs to the number of CPU cores available (leaves 1 for OS stability if > 2)
if [ "$CORES" -gt 2 ]; then
    MAX_JOBS=$((CORES - 1))
else
    MAX_JOBS=$CORES
fi

BASE_ARGS="--sumoConfig=$SUMO_CONFIG "
BASE_ARGS+="--gnbPositions=$GNB_POSITIONS "
BASE_ARGS+="--mecTopology=$MEC_TOPOLOGY "
BASE_ARGS+="--duration=$DURATION "
BASE_ARGS+="--maxUes=$MAX_UES "
BASE_ARGS+="--maxBuses=$MAX_BUSES "
BASE_ARGS+="--maxCars=$MAX_CARS "
BASE_ARGS+="--maxBicycles=$MAX_BICYCLES "
BASE_ARGS+="--fastChannel=$FAST_CHANNEL "

scenarios=(
    "spatial 0 spatial_baseline"
    "mdmkp 1 mdmkp_1s"
    "mdmkp 10 mdmkp_10s"
    "mdmkp 30 mdmkp_30s"
)

echo "=================================================="
echo " Starting ns-3 MEC Experiments Batch (PARALLEL)"
echo " Total Scenarios: ${#scenarios[@]}"
echo " Runs per Scenario: $NUM_RUNS"
echo " Total Executions: $((${#scenarios[@]} * NUM_RUNS))"
echo " Concurrent Workers: $MAX_JOBS (Based on CPU Cores)"
echo "=================================================="

# 1. Build beforehand to prevent parallel lock collisions in waf/ninja
echo ">>> Building ns-3 core..."
./ns3 build

echo ">>> Launching simulations..."
echo ""

# Function to run a single experiment
run_experiment() {
    local strategy=$1
    local interval=$2
    local folder=$3
    local run=$4
    local port=$5

    local OUTPUT_DIR="results/${folder}/run_${run}"
    mkdir -p "$OUTPUT_DIR"
    
    echo "    [START] $folder | Run: $run/$NUM_RUNS | Seed: $run"

    # --no-build is CRUCIAL here to avoid ninja lock crashes during parallel execution
    ./ns3 run --no-build "mec-5g-guimaraes ${BASE_ARGS} --mecStrategy=${strategy} --mdmkpInterval=${interval} --outputDirectory=${OUTPUT_DIR} --sumoPort=${port}" -- --RngRun=$run > "${OUTPUT_DIR}/stdout.log" 2>&1

    if [ $? -eq 0 ]; then
        echo "    [ OK  ] $folder | Run: $run finished."
    else
        echo "    [ERROR] $folder | Run: $run failed! Check ${OUTPUT_DIR}/stdout.log"
    fi
}

# 2. Parallel Queue System
jobs_running=0
port_offset=0

for scenario in "${scenarios[@]}"; do
    read -r strategy interval folder <<< "$scenario"
    for run in $(seq 1 $NUM_RUNS); do
        
        # Launch job in background
        run_experiment "$strategy" "$interval" "$folder" "$run" "$((3400 + port_offset))" &
        ((port_offset++))
        
        ((jobs_running++))
        
        # If we reached the maximum concurrent jobs, wait for at least one to finish
        if [[ $jobs_running -ge $MAX_JOBS ]]; then
            wait -n
            ((jobs_running--))
        fi
        
    done
done

# Wait for all remaining background jobs to complete
wait

echo ""
echo "=================================================="
echo " All parallel experiments finished!"
echo " Check the 'results/' folder for output CSVs."
echo "=================================================="
