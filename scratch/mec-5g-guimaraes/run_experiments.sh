#!/bin/bash

# ==============================================================================
# NS-3 Experiment Runner: MDMKP Orchestration vs Spatial Edge Routing
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

# Build base arguments explicitly with spaces
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
echo " Starting ns-3 MEC Experiments Batch"
echo " Total Scenarios: ${#scenarios[@]}"
echo " Runs per Scenario: $NUM_RUNS"
echo " Duration: $DURATION seconds per run"
echo "=================================================="

./ns3 build

for scenario in "${scenarios[@]}"; do
    read -r strategy interval folder <<< "$scenario"

    echo ""
    echo ">>> Initiating Scenario: $folder (Strategy=$strategy, Interval=${interval}s)"
    
    for run in $(seq 1 $NUM_RUNS); do
        OUTPUT_DIR="results/${folder}/run_${run}"
        mkdir -p "$OUTPUT_DIR"
        
        echo "    -> [Run $run/$NUM_RUNS] | Output: $OUTPUT_DIR | RNG Seed: $run"

        # Execute ns-3 properly forwarding arguments
        ./ns3 run "mec-5g-guimaraes ${BASE_ARGS} --mecStrategy=${strategy} --mdmkpInterval=${interval} --outputDirectory=${OUTPUT_DIR}" -- --RngRun=$run

        if [ $? -eq 0 ]; then
            echo "       [OK] Run $run finished successfully."
        else
            echo "       [ERROR] Run $run failed! Check logs."
            exit 1
        fi
    done
done
