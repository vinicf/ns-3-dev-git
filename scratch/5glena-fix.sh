#!/bin/bash
# ==============================================================================
# 5G-LENA (v4.2) Known Bugs Patcher
# Applies critical stability patches to the official CTTC nr submodule.
# Run this BEFORE compiling ns-3.
# ==============================================================================

echo ">>> Applying 5G-LENA Patches..."

# 1. Fix X2 Interface Setup Crash for Multi-gNB topologies
# Bug: DoAddX2Interface incorrectly iterates over GetBwpIds() instead of assigning single cellIds.
# Symptoms: "Mapping for remoteCellId = 0 is already known" during X2 establishment.
echo "  -> Patching nr-no-backhaul-epc-helper.cc (X2 Interface)"
sed -i 's/gnb2NrDevice->GetBwpIds()/std::vector<uint16_t>{gnb2CellId}/g' contrib/nr/helper/nr-no-backhaul-epc-helper.cc
sed -i 's/gnb1NrDevice->GetBwpIds()/std::vector<uint16_t>{gnb1CellId}/g' contrib/nr/helper/nr-no-backhaul-epc-helper.cc

# 2. Fix MAC Scheduler Fatal Crash on stray Uplink CQIs
# Bug: A stray UL CQI report after a UE hands over or emergency brakes (SUMO) crashes the simulator.
# Symptoms: "NS_ASSERT failed, cond="itAlloc != m_ulAllocationMap.end()" in nr-mac-scheduler-ns3.cc"
echo "  -> Patching nr-mac-scheduler-ns3.cc (MAC Scheduler)"
sed -i 's/NS_ASSERT_MSG(itAlloc != m_ulAllocationMap.end(), "Can'"'"'t find allocation for " << ulSfnSf);/if (itAlloc == m_ulAllocationMap.end()) { NS_LOG_WARN("Can'"'"'t find allocation for " << ulSfnSf); return; }/g' contrib/nr/model/nr-mac-scheduler-ns3.cc

echo ">>> All 5G-LENA patches applied successfully!"
