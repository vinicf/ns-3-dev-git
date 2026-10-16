#!/bin/bash

# ==============================================================================
# NS-3 Experiment Runner: MDMKP Orchestration vs Spatial Edge Routing (PARALLEL)
# ==============================================================================

# Ensure execution happens from the ns-3 root directory
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
NS3_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$NS3_ROOT" || exit 1

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

# Number of stochastic repetitions per scenario (RngRun: 1 .. NUM_RUNS)
NUM_RUNS=10

# Performance & Granularity Adjustments (500ms sync & channel update; disable heavy per-slot traces)
SYNCH_INTERVAL_MS=500
CHANNEL_UPDATE_PERIOD_MS=500
ENABLE_PHY_TRACES="false"

# Determine Number of Concurrent Jobs (Safe by CPU and RAM)
CORES=$(nproc 2>/dev/null || echo 4)
MEM_GB=$(free -g | awk '/^Mem:/{print $2}' 2>/dev/null || echo 4)

# 5G-LENA uses ~1.2 GB to 1.5 GB of RAM per instance with reduced antenna dimensions and disabled PHY traces.
SAFE_JOBS_BY_RAM=$((MEM_GB / 4))
[ "$SAFE_JOBS_BY_RAM" -lt 1 ] && SAFE_JOBS_BY_RAM=1

if [ "$CORES" -gt "$SAFE_JOBS_BY_RAM" ]; then
    MAX_JOBS=$SAFE_JOBS_BY_RAM
    echo ">>> Capping concurrent jobs to $MAX_JOBS due to RAM limits (${MEM_GB}GB total) to prevent OOM."
else
    MAX_JOBS=$((CORES > 1 ? CORES - 1 : 1))
fi

MAX_JOBS=4

BASE_ARGS="--sumoConfig=$SUMO_CONFIG "
BASE_ARGS+="--gnbPositions=$GNB_POSITIONS "
BASE_ARGS+="--mecTopology=$MEC_TOPOLOGY "
BASE_ARGS+="--duration=$DURATION "
BASE_ARGS+="--maxUes=$MAX_UES "
BASE_ARGS+="--maxBuses=$MAX_BUSES "
BASE_ARGS+="--maxCars=$MAX_CARS "
BASE_ARGS+="--maxBicycles=$MAX_BICYCLES "
BASE_ARGS+="--fastChannel=$FAST_CHANNEL "
BASE_ARGS+="--synchIntervalMs=$SYNCH_INTERVAL_MS "
BASE_ARGS+="--channelUpdatePeriodMs=$CHANNEL_UPDATE_PERIOD_MS "
BASE_ARGS+="--enablePhyTraces=$ENABLE_PHY_TRACES "
BASE_ARGS+="--SchedulerType=ns3::PriorityQueueScheduler "

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
echo " Concurrent Workers: $MAX_JOBS"
echo " Synchronization / Channel Interval: ${SYNCH_INTERVAL_MS}ms"
echo "=================================================="

# 1. Clean up any stale SUMO processes from previous aborted runs
echo ">>> Checking and cleaning up any stale SUMO processes on ports 3400+..."
pkill -9 -f "sumo.*--remote-port" 2>/dev/null

cleanup() {
    echo ""
    echo ">>> Interrupt received! Terminating background simulations and cleaning up SUMO..."
    kill $(jobs -p) 2>/dev/null
    pkill -9 -f "sumo.*--remote-port" 2>/dev/null
    exit 1
}
trap cleanup SIGINT SIGTERM

# 2. Build beforehand to prevent parallel lock collisions in waf/ninja
echo ">>> Building ns-3 core..."
./ns3 build

echo ">>> Launching simulations..."
echo ""

run_experiment() {
    local strategy=$1
    local interval=$2
    local folder=$3
    local run=$4
    local port=$5

    local OUTPUT_DIR="results/${folder}/run_${run}"
    mkdir -p "$OUTPUT_DIR"
    
    echo "    [START] $folder | Run: $run/$NUM_RUNS | Seed: $run (Port: $port)"

    ./ns3 run --no-build "mec-5g-guimaraes ${BASE_ARGS} --mecStrategy=${strategy} --mdmkpInterval=${interval} --outputDirectory=${OUTPUT_DIR} --sumoPort=${port}" -- --RngRun=$run > "${OUTPUT_DIR}/stdout.log" 2>&1

    if [ $? -eq 0 ]; then
        echo "    [ OK  ] $folder | Run: $run finished."
    else
        echo "    [ERROR] $folder | Run: $run failed! Check ${OUTPUT_DIR}/stdout.log"
    fi
}

jobs_running=0
port_offset=0

for scenario in "${scenarios[@]}"; do
    read -r strategy interval folder <<< "$scenario"
    for run in $(seq 1 $NUM_RUNS); do
        
        run_experiment "$strategy" "$interval" "$folder" "$run" "$((3400 + port_offset))" &
        ((port_offset++))
        
        ((jobs_running++))
        if [[ $jobs_running -ge $MAX_JOBS ]]; then
            wait -n
            ((jobs_running--))
        fi
    done
done

wait

echo ""
echo "=================================================="
echo " All parallel experiments finished!"
echo " Check the 'results/' folder for output CSVs."
echo "=================================================="
