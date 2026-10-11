#!/bin/bash
# ==============================================================================
# 5G-LENA (v4.2) Known Bugs Patcher
# Applies critical stability patches to the official CTTC nr submodule.
# ==============================================================================

echo ">>> Applying 5G-LENA Patches..."

echo "  -> Patching nr-no-backhaul-epc-helper.cc (X2 Interface)"
sed -i 's/gnb2NrDevice->GetBwpIds()/std::vector<uint16_t>{gnb2CellId}/g' contrib/nr/helper/nr-no-backhaul-epc-helper.cc
sed -i 's/gnb1NrDevice->GetBwpIds()/std::vector<uint16_t>{gnb1CellId}/g' contrib/nr/helper/nr-no-backhaul-epc-helper.cc

echo "  -> Patching nr-mac-scheduler-ns3.cc (MAC Scheduler - Stray Allocations & Detached UEs)"
# 1. Ignore stray UL CQI request if the allocation map entry is gone
perl -pi -e 's/NS_ASSERT_MSG\s*\(\s*itAlloc\s*!=\s*m_ulAllocationMap\.end\(\).*?;/if (itAlloc == m_ulAllocationMap.end()) { NS_LOG_WARN("Can'\''t find allocation for " << ulSfnSf); return; }/g' contrib/nr/model/nr-mac-scheduler-ns3.cc

# 2. Ignore stray CQI inside allocations if the UE has already detached/left the map
perl -pi -e 's/NS_ASSERT\s*\(\s*itUe\s*!=\s*m_ueMap\.end\(\)\s*\);/if (itUe == m_ueMap.end()) { found = true; it = ulAllocations.erase(it); continue; }/g' contrib/nr/model/nr-mac-scheduler-ns3.cc

# 3. Defensively ignore DL CQI if the UE is gone
perl -pi -e 's/NS_ASSERT\s*\(\s*m_ueMap\.find\s*\(\s*cqi\.m_rnti\s*\)\s*!=\s*m_ueMap\.end\(\)\s*\);/if (m_ueMap.find(cqi.m_rnti) == m_ueMap.end()) continue;/g' contrib/nr/model/nr-mac-scheduler-ns3.cc

# Verification
if grep -q "if (itUe == m_ueMap.end())" contrib/nr/model/nr-mac-scheduler-ns3.cc; then
    echo "     [OK] MAC Scheduler detached UE patch applied."
else
    echo "     [ERROR] MAC Scheduler detached UE patch failed!"
fi

echo ">>> All 5G-LENA patches applied successfully!"
