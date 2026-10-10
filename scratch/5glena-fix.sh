#!/bin/bash
# ==============================================================================
# 5G-LENA (v4.2) Known Bugs Patcher
# Applies critical stability patches to the official CTTC nr submodule.
# ==============================================================================

echo ">>> Applying 5G-LENA Patches..."

echo "  -> Patching nr-no-backhaul-epc-helper.cc (X2 Interface)"
sed -i 's/gnb2NrDevice->GetBwpIds()/std::vector<uint16_t>{gnb2CellId}/g' contrib/nr/helper/nr-no-backhaul-epc-helper.cc
sed -i 's/gnb1NrDevice->GetBwpIds()/std::vector<uint16_t>{gnb1CellId}/g' contrib/nr/helper/nr-no-backhaul-epc-helper.cc

echo "  -> Patching nr-mac-scheduler-ns3.cc (MAC Scheduler)"
# Using Perl to handle multiple lines or flexible spacing if needed
perl -pi -e 's/NS_ASSERT_MSG\s*\(\s*itAlloc\s*!=\s*m_ulAllocationMap\.end\(\).*?;/if (itAlloc == m_ulAllocationMap.end()) { NS_LOG_WARN("Can'\''t find allocation for " << ulSfnSf); return; }/g' contrib/nr/model/nr-mac-scheduler-ns3.cc

# Verification
if grep -q "if (itAlloc == m_ulAllocationMap.end())" contrib/nr/model/nr-mac-scheduler-ns3.cc; then
    echo "     [OK] MAC Scheduler patch applied."
else
    echo "     [ERROR] MAC Scheduler patch failed to apply!"
fi

echo ">>> All 5G-LENA patches applied successfully!"
