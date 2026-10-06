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
FAST_CHANNEL="true" # Mantém a otimização estatística do canal ativada

# Statistical Runs
NUM_RUNS=5

# Base arguments injected into all runs
BASE_ARGS="--sumoConfig=$SUMO_CONFIG \
           --gnbPositions=$GNB_POSITIONS \
           --mecTopology=$MEC_TOPOLOGY \
           --duration=$DURATION \
           --maxUes=$MAX_UES \
           --maxBuses=$MAX_BUSES \
           --maxCars=$MAX_CARS \
           --maxBicycles=$MAX_BICYCLES \
           --fastChannel=$FAST_CHANNEL"

# Define Scenarios array
# Format: "Strategy Interval OutputFolderName"
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

# Build the ns-3 project once before starting the massive loops
./ns3 build

for scenario in "${scenarios[@]}"; do
    # Parse the scenario variables
    read -r strategy interval folder <<< "$scenario"

    echo ""
    echo ">>> Initiating Scenario: $folder (Strategy=$strategy, Interval=${interval}s)"
    
    for run in $(seq 1 $NUM_RUNS); do
        OUTPUT_DIR="results/${folder}/run_${run}"
        
        # Ensure output directory exists (optional, C++ might create it, but safe)
        mkdir -p "$OUTPUT_DIR"
        
        echo "    -> [Run $run/$NUM_RUNS] | Output: $OUTPUT_DIR | RNG Seed: $run"

        # Execute ns-3 (Passing --RngRun OUTSIDE the quoted string for ns-3 core)
        ./ns3 run "mec-5g-guimaraes $BASE_ARGS \
                   --mecStrategy=$strategy \
                   --mdmkpInterval=$interval \
                   --outputDirectory=$OUTPUT_DIR" \
                   --RngRun=$run

        # Basic check to see if ns3 crashed or finished properly
        if [ $? -eq 0 ]; then
            echo "       [OK] Run $run finished successfully."
        else
            echo "       [ERROR] Run $run failed! Check logs."
            exit 1
        fi
    done
done

echo ""
echo "=================================================="
echo " All experiments completed successfully!"
echo " Check the 'results/' folder for your CSV files."
echo "=================================================="
